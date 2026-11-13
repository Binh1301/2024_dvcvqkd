"""Independent deterministic availability classification; never computes SKR.

Array axes remain [t,y,x]. Unknown blockage=255 is separate from 0/1.
qkd_available is fail-closed Boolean: unknown is never True; resolved_mask
must accompany it to distinguish unknown from known unavailability.
"""
import numpy as np

UNKNOWN=np.uint8(255)
VALIDATED_INPUT=np.uint8(0)
CLEAR_UNAVAILABLE=np.uint8(1)
UNRESOLVED=np.uint8(2)
DIAGNOSTIC_ASSUMED=np.uint8(3)


def classify_attenuation(attenuation_db,threshold_db,clear_sky_state,*,mode):
    """Classify supplied thresholds; 'validated_input' is a caller assertion only.

    This function cannot validate a QKD model. The delivered runner exports only
    a diagnostic threshold and an official-pending state, never validated roots.
    clear_sky_state is 0=known unavailable,1=known feasible,255=unknown.
    """
    if mode not in ['diagnostic','validated_input']:
        raise ValueError('Explicit threshold interpretation required')
    a=np.asarray(attenuation_db,dtype=np.float64)
    if a.ndim!=3 or any(n<=0 for n in a.shape):raise ValueError('Require nonempty [t,y,x] attenuation')
    shape=a.shape[1:]
    th=np.asarray(threshold_db,dtype=np.float64)
    if th.ndim==0:th=np.full(shape,float(th))
    if th.shape!=shape:raise ValueError('Threshold shape must match [y,x]')
    cs=np.asarray(clear_sky_state)
    if cs.ndim==0:cs=np.full(shape,cs.item())
    if cs.shape!=shape or not np.isin(cs,[0,1,255]).all():raise ValueError('Invalid tri-state clear-sky map')
    cs=cs.astype(np.uint8,copy=True)
    static=np.full(shape,UNRESOLVED,dtype=np.uint8)
    baseline=cs==0
    eligible=(cs==1)&np.isfinite(th)&(th>0)
    static[baseline]=CLEAR_UNAVAILABLE
    static[eligible]=DIAGNOSTIC_ASSUMED if mode=='diagnostic' else VALIDATED_INPUT
    resolved=np.broadcast_to(baseline,a.shape).copy() | (eligible[None,:,:]&np.isfinite(a)&(a>=0))
    b=np.full(a.shape,UNKNOWN,dtype=np.uint8)
    b[:,baseline]=1
    active=eligible[None,:,:]&np.isfinite(a)&(a>=0)
    np.copyto(b,(a>=th[None,:,:]).astype(np.uint8),where=active)
    return dict(binary_blockage=b,qkd_available=(b==0),resolved_mask=resolved,
                clear_sky_available=cs,classification_status=static)


def frame_statistics(attenuation_db,classification):
    a=np.asarray(attenuation_db,dtype=float);b=classification['binary_blockage']
    if a.shape!=b.shape:raise ValueError('Shape mismatch')
    clear=classification['clear_sky_available']==1
    rows=[]
    for k in range(len(a)):
        known=b[k]!=UNKNOWN;affected=np.isfinite(a[k])&(a[k]>0)
        condition=known&clear
        cloud_blocked=condition&affected&(b[k]==1)
        count=int(condition.sum());clear_count=int(clear.sum())
        affected_count=int((clear&affected).sum())
        affected_resolved=int((condition&affected).sum())
        rows.append(dict(slot=k,cell_count=b[k].size,resolved_cells=int(known.sum()),
            blocked_cells=int(np.sum(b[k]==1)),available_cells=int(np.sum(b[k]==0)),
            unresolved_cells=int(np.sum(~known)),
            blockage_ratio=float(np.mean(b[k]==1)) if known.all() else None,
            known_blocked_lower_fraction=float(np.mean(b[k]==1)),
            unresolved_fraction=float(np.mean(~known)),
            clear_sky_known_feasible_resolved_cells=count,
            clear_sky_known_feasible_cells=clear_count,
            cloud_induced_blocked_cells=int(cloud_blocked.sum()),
            cloud_induced_ratio_given_clear=float(cloud_blocked.sum()/clear_count) if clear_count and count==clear_count else None,
            cloud_affected_clear_cells=affected_count,
            cloud_affected_clear_resolved_cells=affected_resolved,
            blocked_ratio_given_cloud_affected_clear=float(cloud_blocked.sum()/affected_count) if affected_count and affected_resolved==affected_count else None))
    return rows


def binary_effective_approximations(binary_blockage,clear_transmittance,clear_usable_rate):
    """Optional approximation only; never overwrites physical cloud transmittance."""
    b=np.asarray(binary_blockage)
    if b.ndim!=3 or not np.isin(b,[0,1]).all():raise ValueError('Fully resolved binary field required')
    t,r=np.asarray(clear_transmittance,float),np.asarray(clear_usable_rate,float)
    if t.shape!=b.shape[1:] or r.shape!=t.shape:raise ValueError('Clear maps must have [y,x] shape')
    if not np.isfinite(t).all() or np.any((t<0)|(t>1)) or not np.isfinite(r).all() or np.any(r<0):
        raise ValueError('Physical clear transmittance and nonnegative usable rate required')
    available=b==0
    return dict(T_binary_approximation=available*t[None,:,:],R_binary_approximation=available*r[None,:,:])
