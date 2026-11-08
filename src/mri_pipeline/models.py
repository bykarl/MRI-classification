"""D/S/Z/F/U/R with training-only transforms and grouped cross-fitting.

This is a research implementation, not evidence of clinical/model performance.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, confusion_matrix
from .io import array_finite
from .features import formal_eligibility

MODEL_NAMES = ('D', 'S', 'Z', 'F', 'U', 'R')


def subset(data, indices):
    n = len(data['label'])
    return {k: (v[indices] if isinstance(v, np.ndarray) and v.ndim and len(v)==n else v) for k,v in data.items()}


def splits(y, groups, n_splits, seed):
    y, groups = np.asarray(y), np.asarray(groups)
    if len(y) != len(groups) or set(y) != {0,1} or any(not str(g).strip() for g in groups):
        raise ValueError('Binary labels and nonempty natural-person groups required')
    for group in np.unique(groups):
        if len(np.unique(y[groups == group])) != 1:
            raise ValueError('Conflicting labels in a natural-person group')
    if n_splits < 2 or min(len(set(groups[y==label])) for label in (0,1)) < n_splits:
        raise ValueError('Insufficient independent people per class for requested folds')
    # Stratify the independent unit itself, not a heuristic balance of visits.
    people, first = np.unique(groups, return_index=True)
    cv = StratifiedKFold(n_splits, shuffle=True, random_state=seed)
    result = [(np.flatnonzero(np.isin(groups,people[tr])), np.flatnonzero(np.isin(groups,people[va])))
              for tr,va in cv.split(np.zeros(len(people)),y[first])]
    for train, valid in result:
        if set(groups[train]) & set(groups[valid]) or len(set(y[train]))!=2 or len(set(y[valid]))!=2:
            raise ValueError('Invalid group/class split; revise fold plan after QC')
    return result


def balanced_weights(y):
    y = np.asarray(y)
    return len(y)/(2*np.bincount(y, minlength=2)[y])


class FoldTransform:
    """Demographic encoders, ICV adjustment and scales fit only on this path."""
    @staticmethod
    def categorical(data):
        return np.column_stack([np.asarray(data[k], dtype=str) for k in ('sex','education_code')])

    def raw_s(self, data):
        parts = []
        if 's_t1_raw' in data:
            v = array_finite(data['s_t1_raw'], ndim=2)
            icv = array_finite(data['icv_mm3'], ndim=1)
            if v.shape[1] != 82 or np.any(icv<=0):
                raise ValueError('82 T1 volumes and positive ICV are required')
            parts.append(v - (icv[:,None]-self.icv_mean)*self.icv_slope)
        if 's_fmri' in data:
            f = array_finite(data['s_fmri'], ndim=2)
            if f.shape[1] != 77:
                raise ValueError('Expected 77 FC summaries')
            parts.append(f)
        if not parts:
            raise ValueError('No interpretable imaging measurements')
        return np.column_stack(parts)

    def fit(self, data):
        age = np.asarray(data['age'], dtype=float).reshape(-1,1)
        if np.isinf(age).any() or np.isnan(age).all():
            raise ValueError('Training age must contain usable values')
        self.age_imputer = SimpleImputer(strategy='median').fit(age)
        self.age_scale = StandardScaler().fit(self.age_imputer.transform(age))
        self.category = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(self.categorical(data))
        if 's_t1_raw' in data:
            v = array_finite(data['s_t1_raw'], ndim=2)
            icv = array_finite(data['icv_mm3'], ndim=1)
            self.icv_mean = float(icv.mean())
            centered = icv-self.icv_mean
            denom = centered@centered
            self.icv_slope = centered@v/denom if denom>0 else np.zeros(v.shape[1])
        self.s_scale = StandardScaler().fit(self.raw_s(data))
        return self

    def transform(self, data):
        age = np.asarray(data['age'], dtype=float).reshape(-1,1)
        c = np.column_stack([self.age_scale.transform(self.age_imputer.transform(age)), self.category.transform(self.categorical(data))])
        s = self.s_scale.transform(self.raw_s(data))
        z = np.column_stack([array_finite(data[k], ndim=2) for k in ('z_t1','z_fmri') if k in data])
        return c, np.column_stack([s,c]), z


class OffsetMLP:
    """One-hidden-layer tanh MLP, weighted BCE, fixed epochs, optional fixed logit.

    sklearn's MLPClassifier cannot train with a fixed baseline offset; explicit
    gradients implement sigmoid(offset + h(x)) rather than stacking probabilities.
    """
    def __init__(self, width=8, epochs=200, lr=0.01, l2=0.001, seed=42):
        self.width, self.epochs, self.lr, self.l2, self.seed = width, epochs, lr, l2, seed

    def fit(self, x, y, offset=None):
        x = array_finite(x, ndim=2)
        self.scale = StandardScaler().fit(x)
        x = self.scale.transform(x)
        y = np.asarray(y, dtype=float)
        offset = np.zeros(len(y)) if offset is None else array_finite(offset, ndim=1)
        w = balanced_weights(y.astype(int)); w /= w.sum()
        rng = np.random.default_rng(self.seed)
        self.params = [rng.normal(0, 1/np.sqrt(x.shape[1]), (x.shape[1],self.width)),
                       np.zeros(self.width), rng.normal(0, 1/np.sqrt(self.width), self.width), np.zeros(1)]
        m = [np.zeros_like(p) for p in self.params]; v = [np.zeros_like(p) for p in self.params]
        for step in range(1,self.epochs+1):
            a,b,c,d = self.params
            hidden = np.tanh(x@a+b)
            prediction = expit(offset+hidden@c+d[0])
            delta = (prediction-y)*w
            dh = delta[:,None]*c*(1-hidden**2)
            grads = [x.T@dh+self.l2*a, dh.sum(0), hidden.T@delta+self.l2*c, np.array([delta.sum()])]
            for i,g in enumerate(grads):
                m[i] = 0.9*m[i]+0.1*g; v[i] = 0.999*v[i]+0.001*g*g
                self.params[i] -= self.lr*(m[i]/(1-0.9**step))/(np.sqrt(v[i]/(1-0.999**step))+1e-8)
        if not all(np.isfinite(p).all() for p in self.params):
            raise ValueError('Nonfinite MLP parameters')
        return self

    def logit(self, x):
        a,b,c,d = self.params
        return np.tanh(self.scale.transform(x)@a+b)@c+d[0]


@dataclass(frozen=True)
class Parameters:
    logistic_c: float = 1.0
    ridge_alpha: float = 10.0
    width: int = 8
    epochs: int = 200
    learning_rate: float = 0.01
    mlp_l2: float = 0.001

    def __post_init__(self):
        if self.logistic_c<=0 or self.ridge_alpha<=0 or self.width<1 or self.epochs<1 or self.learning_rate<=0 or self.mlp_l2<0:
            raise ValueError('Invalid model hyperparameters')


class CrossfitModels:
    """Shared b paths for U/R, OOF training for h, path-probability averaging."""
    def __init__(self, params=None, crossfit_folds=3, seed=42):
        self.params = params or Parameters()
        self.crossfit_folds, self.seed = crossfit_folds, seed

    def mlp(self, seed):
        p = self.params
        return OffsetMLP(p.width,p.epochs,p.learning_rate,p.mlp_l2,seed)

    def fit(self, data):
        y, groups = data['label'], data['person_id']
        fold_indices = splits(y,groups,self.crossfit_folds,self.seed)
        all_z = np.column_stack([data[k] for k in ('z_t1','z_fmri') if k in data])
        residuals = np.empty_like(all_z, dtype=float); offsets = np.empty(len(y))
        self.paths, self.audit = [], []
        for i,(train,valid) in enumerate(fold_indices):
            tr, va = subset(data,train), subset(data,valid)
            transform = FoldTransform().fit(tr)
            c,x,z = transform.transform(tr)
            cv,xv,zv = transform.transform(va)
            b = LogisticRegression(C=self.params.logistic_c, class_weight='balanced', max_iter=2000).fit(x,y[train])
            d = LogisticRegression(C=self.params.logistic_c, class_weight='balanced', max_iter=2000).fit(c,y[train])
            zscale = StandardScaler().fit(z)
            g = Ridge(alpha=self.params.ridge_alpha).fit(x,zscale.transform(z))
            residuals[valid] = zv-zscale.inverse_transform(g.predict(xv))
            offsets[valid] = b.decision_function(xv)
            zm = self.mlp(self.seed+i).fit(np.column_stack([z,c]),y[train])
            fm = self.mlp(self.seed+i).fit(np.column_stack([x,z]),y[train])
            self.paths.append(dict(transform=transform,b=b,d=d,zscale=zscale,g=g,zm=zm,fm=fm))
            self.audit.append({'fit_people': sorted(set(map(str,groups[train]))),
                               'heldout_people': sorted(set(map(str,groups[valid])))})
        self.oof_offsets_, self.oof_residuals_ = offsets, residuals
        # Identical initialization/training budgets, same fixed b logits.
        self.u = self.mlp(self.seed).fit(all_z,y,offsets)
        self.r = self.mlp(self.seed).fit(residuals,y,offsets)
        return self

    def predict(self, data):
        paths = []
        for p in self.paths:
            c,x,z = p['transform'].transform(data)
            base = p['b'].decision_function(x)
            residual = z-p['zscale'].inverse_transform(p['g'].predict(x))
            paths.append(np.column_stack([p['d'].predict_proba(c)[:,1], expit(base),
                expit(p['zm'].logit(np.column_stack([z,c]))), expit(p['fm'].logit(np.column_stack([x,z]))),
                expit(base+self.u.logit(z)), expit(base+self.r.logit(residual))]))
        return np.mean(paths,axis=0)


def person_predictions(y, probabilities, groups):
    keys = np.unique(groups)
    labels, values = [], []
    for g in keys:
        where = np.asarray(groups)==g
        if len(set(np.asarray(y)[where])) != 1:
            raise ValueError('Conflicting labels within person')
        labels.append(np.asarray(y)[where][0]); values.append(np.asarray(probabilities)[where].mean(0))
    return keys, np.asarray(labels), np.asarray(values)


def nested_evaluate(data, candidates, *, outer_folds, inner_folds, crossfit_folds,
                    repeats, paired_selection_rule, seed=42, synthetic=False):
    """Explicit fold counts and paired tuning rule required; no automatic 22-fit run.

    D/S/Z/F tune independently; U/R choose one shared setting using the explicitly
    requested mean inner U/R AUC, preserving a shared b and matched h budget.
    This tuning rule must be confirmed before use on the formal cohort.
    """
    if synthetic:
        if data.get('data_kind') != 'synthetic':
            raise ValueError('Synthetic bypass requires an explicitly tagged test dataset')
    else:
        formal_eligibility(data)
    if paired_selection_rule != 'mean_inner_U_R_auc' or not candidates:
        raise ValueError('Explicitly confirm paired U/R tuning rule and candidates first')
    if repeats < 1:
        raise ValueError('Positive repeat count required')
    y,groups = data['label'],data['person_id']
    predictions = np.empty((repeats,len(y),6)); thresholds = np.empty_like(predictions)
    audit = []
    for repeat in range(repeats):
        for fold,(train,test) in enumerate(splits(y,groups,outer_folds,seed+repeat)):
            tr,te = subset(data,train),subset(data,test)
            inner = splits(tr['label'],tr['person_id'],inner_folds,seed+repeat*100+fold)
            scores, inner_outputs = [], []
            for candidate in candidates:
                oof = np.empty((len(train),6))
                for it,iv in inner:
                    model = CrossfitModels(candidate,crossfit_folds,seed+fold).fit(subset(tr,it))
                    oof[iv] = model.predict(subset(tr,iv))
                _,iy,ip = person_predictions(tr['label'],oof,tr['person_id'])
                scores.append([roc_auc_score(iy,ip[:,m]) for m in range(6)])
                inner_outputs.append((iy,ip))
            scores = np.asarray(scores)
            selected = np.argmax(scores,axis=0)
            paired = int(np.argmax(scores[:,4:6].mean(axis=1)))
            selected[4:] = paired
            fitted = {}
            fold_audit = []
            for m,best in enumerate(selected):
                best = int(best)
                if best not in fitted:
                    fitted[best] = CrossfitModels(candidates[best],crossfit_folds,seed+fold).fit(tr)
                    fold_audit.extend(fitted[best].audit)
                predictions[repeat,test,m] = fitted[best].predict(te)[:,m]
                iy,ip = inner_outputs[best]
                options = np.unique(np.r_[0.,ip[:,m],1.])
                # Threshold selected exclusively from inner out-of-fold predictions.
                threshold = max(options, key=lambda t: (balanced_accuracy_score(iy,ip[:,m]>=t),-abs(t-0.5)))
                thresholds[repeat,test,m] = threshold
            audit.append({'repeat':repeat,'outer_fold':fold,'train_people':sorted(set(map(str,groups[train]))),
                'test_people':sorted(set(map(str,groups[test]))),'selected_candidates':selected.tolist(),
                'crossfit_paths':fold_audit})
    metrics = []
    for repeat in range(repeats):
        _, labels, probs = person_predictions(y,predictions[repeat],groups)
        # A person's repeated visits share the same outer threshold; aggregate
        # probabilities first to keep the metric unit at natural-person level.
        _,_,th = person_predictions(y,thresholds[repeat],groups)
        row = {}
        for m,name in enumerate(MODEL_NAMES):
            cls = probs[:,m]>=th[:,m]
            tn,fp,fn,tp = confusion_matrix(labels,cls,labels=[0,1]).ravel()
            row[name] = {'roc_auc':float(roc_auc_score(labels,probs[:,m])),
                         'balanced_accuracy':float(balanced_accuracy_score(labels,cls)),
                         'sensitivity':float(tp/(tp+fn)), 'specificity':float(tn/(tn+fp))}
        metrics.append(row)
    return {'probabilities':predictions,'thresholds':thresholds,'metrics':metrics,
            'audit':audit,'data_kind':'synthetic' if synthetic else 'formal',
            'model_names':MODEL_NAMES,'paired_selection_rule':paired_selection_rule}


def bootstrap_auc(y, probabilities, groups, *, n_boot=1000, seed=42):
    """Person-paired, class-stratified bootstrap of FIXED held-out predictions.

    probabilities: [repeat, record, model]. Repeats are kept together, never
    treated as new people. Does not capture full retraining uncertainty.
    """
    p = array_finite(probabilities, ndim=3)
    if n_boot < 2:
        raise ValueError('At least two bootstrap draws required')
    by_repeat = [person_predictions(y,r,groups) for r in p]
    labels = by_repeat[0][1]
    values = np.stack([r[2] for r in by_repeat])
    rng = np.random.default_rng(seed); scores=[]
    for _ in range(n_boot):
        idx = np.concatenate([rng.choice(np.flatnonzero(labels==c),sum(labels==c),replace=True) for c in (0,1)])
        scores.append(np.mean([[roc_auc_score(labels[idx],r[idx,m]) for m in range(values.shape[2])] for r in values],axis=0))
    scores=np.asarray(scores)
    return {'auc_interval_95':np.quantile(scores,[.025,.975],axis=0),
            'R_minus_F_interval_95':np.quantile(scores[:,5]-scores[:,3],[.025,.975]),
            'R_minus_U_interval_95':np.quantile(scores[:,5]-scores[:,4],[.025,.975]),
            'limitation':'Descriptive intervals from fixed predictions; excludes full training uncertainty.'}
