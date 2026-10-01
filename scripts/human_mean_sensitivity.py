"""Outcome-aware secondary arithmetic-mean aggregator; primary code unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import human_extension as base
import numpy as np

ORIGINAL=base.representations
def plus_mean(train,test,visible,incidence,families,seed):
    values=ORIGINAL(train,test,visible,incidence,families,seed)
    keep=np.isfinite(train).mean(axis=0)>=.8
    names=list(np.asarray(visible)[keep])
    a,b,_,_=base.standardize(train[:,keep],test[:,keep])
    member=incidence.loc[names]
    member=member.loc[:,member.sum(axis=0).ge(2)]
    weights=member.to_numpy(dtype=float)
    weights=weights/weights.sum(axis=0)
    x,z,_,_=base.standardize(a@weights,b@weights)
    budget=values['structural_median'][2].copy()
    values['descriptor_mean']=(x,z,budget)
    return values

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--dataset',required=True,choices=['st002081','st000818'])
    args=parser.parse_args()
    wrapper_hash=base.sha(__file__)
    base.MODELS=(*base.MODELS,'descriptor_mean')
    base.representations=plus_mean
    path=base.ROOT/f'runs/m2-human-mean-secondary-v2-{args.dataset}'
    result=base.run(args.dataset,'primary',path)
    assert base.sha(__file__)==wrapper_hash
    result.update(secondary_outcome_aware=True,wrapper_sha256=wrapper_hash,
                  secondary_amendment_sha256=base.sha(base.ROOT/'readiness/m2-amendment-mean-secondary-v1.md'),
                  wrapper_effect='adds training-standardized arithmetic mean on identical descriptor memberships; all primary models retained')
    (path/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
