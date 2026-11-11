"""Synthetic exponential-covariance GRF + wind + AR(1); no optical/QKD model."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.fft import rfft2, irfft2, next_fast_len
from scipy.ndimage import label
from scipy.special import ndtri

MODEL_NAME = "Spatiotemporal Stochastic Cloud Field Model using Spatially Correlated GRF, Wind Advection and AR(1) Temporal Evolution"


@dataclass(frozen=True)
class GRFConfig:
    nx: int = 50
    ny: int = 50
    dx_m: float = 40.0
    dy_m: float = 40.0
    dt_s: float = 1.0
    slots: int = 1000
    vx_m_s: float = -5.0
    vy_m_s: float = 0.0
    ell_c_m: float = 200.0
    tau_c_s: float = 300.0
    seed: int = 20261111
    refine_x: int = 8
    refine_y: int = 1
    guard_m: float = 1000.0
    embedding_scale: int = 1
    initial_fraction: float = .30
    threshold_mode: str = "ensemble"
    theta_c: float | None = None
    A: float = 1.0
    q: float = 1.0
    tracking_iou: float = .10

    def __post_init__(self):
        for name in ("nx", "ny", "slots", "refine_x", "refine_y", "embedding_scale"):
            if type(getattr(self,name)) is not int or getattr(self,name)<=0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.seed) is not int or self.seed<0:
            raise ValueError("seed must be a nonnegative integer")
        for name in ("dx_m","dy_m","dt_s","vx_m_s","vy_m_s","ell_c_m","tau_c_s","guard_m","initial_fraction","A","q","tracking_iou"):
            x=getattr(self,name)
            if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
                raise ValueError(f"{name} must be finite numeric")
        if min(self.dx_m,self.dy_m,self.dt_s,self.ell_c_m,self.tau_c_s,self.guard_m,self.A,self.q)<=0:
            raise ValueError("spacings, dt, ell, tau, guard, A and q must be positive")
        if not 0<self.initial_fraction<1 or not 0<self.tracking_iou<1:
            raise ValueError("fraction and tracking IoU must be in (0,1)")
        if self.threshold_mode not in ("ensemble","initial","fixed"):
            raise ValueError("unknown threshold mode")
        if self.threshold_mode=="fixed" and (self.theta_c is None or not math.isfinite(self.theta_c)):
            raise ValueError("fixed mode requires finite theta_c")
        _integer(self.vx_m_s*self.dt_s/(self.dx_m/self.refine_x))
        _integer(self.vy_m_s*self.dt_s/(self.dy_m/self.refine_y))

    @property
    def rho(self):
        return math.exp(-self.dt_s/self.tau_c_s)

    @property
    def alpha(self):
        return math.sqrt(-math.expm1(-2*self.dt_s/self.tau_c_s))


def _integer(value):
    if not math.isfinite(value) or not np.isclose(value,round(value),atol=1e-10,rtol=0):
        raise ValueError("wind displacement must be integral on the internal grid; increase refinement, never round physical motion")
    return round(value)


def checked_eigenvalues(spectrum):
    spectrum=np.asarray(spectrum)
    if not np.isfinite(spectrum).all():
        raise ValueError("nonfinite circulant spectrum")
    if abs(spectrum.imag).max()>1e-10*max(1.,abs(spectrum).max()):
        raise ValueError("circulant covariance spectrum is not real")
    eigen=spectrum.real.copy()
    if eigen.min()<0:
        raise ValueError(f"non-positive-semidefinite embedding: minimum eigenvalue {eigen.min()}; no clipping allowed")
    return eigen


class CirculantGRF:
    """Exact exponential covariance on required grid stencils; positive FFT embedding."""
    def __init__(self,c):
        self.c=c
        self.dx=c.dx_m/c.refine_x;self.dy=c.dy_m/c.refine_y
        self.step_x=_integer(c.vx_m_s*c.dt_s/self.dx)
        self.step_y=_integer(c.vy_m_s*c.dt_s/self.dy)
        self.horizon=c.slots*c.dt_s
        # Twice the complete ROI/travel span plus guard also protects covariance
        # differences from minimum-image folding, beyond preventing cloud re-entry.
        self.nx=next_fast_len(math.ceil(2*(c.nx*c.dx_m+abs(c.vx_m_s)*self.horizon+c.guard_m)/self.dx)*c.embedding_scale,real=True)
        self.ny=next_fast_len(math.ceil(2*(c.ny*c.dy_m+abs(c.vy_m_s)*self.horizon+c.guard_m)/self.dy)*c.embedding_scale,real=True)
        self.shape=self.ny,self.nx
        self.x0=math.ceil((c.guard_m+max(c.vx_m_s,0)*self.horizon+c.dx_m/2)/self.dx)
        self.y0=math.ceil((c.guard_m+max(c.vy_m_s,0)*self.horizon+c.dy_m/2)/self.dy)
        self.ix=self.x0+np.arange(c.nx)*c.refine_x
        self.iy=self.y0+np.arange(c.ny)*c.refine_y
        x=np.minimum(np.arange(self.nx),self.nx-np.arange(self.nx))*self.dx
        y=np.minimum(np.arange(self.ny),self.ny-np.arange(self.ny))*self.dy
        self.kernel=np.exp(-np.hypot(y[:,None],x[None,:])/c.ell_c_m)
        spectrum=rfft2(self.kernel,workers=1)
        eigen=checked_eigenvalues(spectrum)
        self.sqrt_eigen=np.sqrt(eigen)
        self.spectrum_receipt={"minimum_eigenvalue":float(eigen.min()),"maximum_eigenvalue":float(eigen.max()),
                               "negative_eigenvalues":0,"clipped_eigenvalues":0,"max_imaginary_residual":float(abs(spectrum.imag).max()),
                               "covariance_reconstruction_max_error":float(abs(irfft2(eigen,s=self.shape,workers=1)-self.kernel).max()),
                               "target_marginal_variance":float(self.kernel[0,0])}

    def draw(self,rng):
        spectrum=rfft2(rng.standard_normal(self.shape),workers=1)
        spectrum*=self.sqrt_eigen
        return irfft2(spectrum,s=self.shape,workers=1)

    def sample(self,field,offset_x=0,offset_y=0,*,material_slot=None):
        if field.shape!=self.shape:
            raise ValueError("wrong internal field shape")
        ix=self.ix+_integer(offset_x/self.dx)
        iy=self.iy+_integer(offset_y/self.dy)
        if material_slot is not None:
            ix=ix+self.step_x*(material_slot-(self.c.slots-1))
            iy=iy+self.step_y*(material_slot-(self.c.slots-1))
        if min(ix)<0 or max(ix)>=self.nx or min(iy)<0 or max(iy)>=self.ny:
            raise ValueError("unwrapped sampling exceeded synthetic domain")
        return field[np.ix_(iy,ix)].copy()

    def advect(self,field,slots=1):
        return np.roll(field,(self.step_y*slots,self.step_x*slots),axis=(0,1))

    def covariance(self,hx,hy,lag=0):
        return self.c.rho**lag*math.exp(-math.hypot(hx-self.c.vx_m_s*lag*self.c.dt_s,
                                                  hy-self.c.vy_m_s*lag*self.c.dt_s)/self.c.ell_c_m)

    def embedded_covariance(self,hx,hy,lag=0):
        ix=_integer((hx-self.c.vx_m_s*lag*self.c.dt_s)/self.dx)
        iy=_integer((hy-self.c.vy_m_s*lag*self.c.dt_s)/self.dy)
        return self.c.rho**lag*float(self.kernel[iy%self.ny,ix%self.nx])

    def expected_roi_variance(self):
        total=0.
        for dy in range(-self.c.ny+1,self.c.ny):
            for dx in range(-self.c.nx+1,self.c.nx):
                total+=(self.c.ny-abs(dy))*(self.c.nx-abs(dx))*self.covariance(dx*self.c.dx_m,dy*self.c.dy_m)
        return 1-total/(self.c.nx*self.c.ny)**2

    def boundary_receipt(self):
        rows=[]
        for time in sorted(set([0.,min(400.,self.horizon),(self.c.slots-1)*self.c.dt_s,self.horizon])):
            row={"time_s":time}
            for axis,first,width,spacing,velocity,n in (
                ("x",self.x0*self.dx,self.c.nx*self.c.dx_m,self.c.dx_m,self.c.vx_m_s,self.nx*self.dx),
                ("y",self.y0*self.dy,self.c.ny*self.c.dy_m,self.c.dy_m,self.c.vy_m_s,self.ny*self.dy)):
                lo=first-spacing/2-velocity*time;hi=lo+width
                row[axis+"_backtrace_edges_m"]=[lo,hi]
                row[axis+"_margin_m"]=min(lo,n-hi)
            rows.append(row)
        passed=min(r[a+"_margin_m"] for r in rows for a in ("x","y"))>=self.c.guard_m-1e-9
        return {"status":"CURRENTLY_VERIFIED_PASS" if passed else "FAILED","internal_shape_yx":list(self.shape),
                "internal_spacing_xy_m":[self.dx,self.dy],"synthetic_extent_xy_m":[self.nx*self.dx,self.ny*self.dy],
                "sampling_origin_indices_yx":[self.y0,self.x0],"step_internal_yx":[self.step_y,self.step_x],
                "output_displacement_xy_cells":[self.c.vx_m_s*self.c.dt_s/self.c.dx_m,self.c.vy_m_s*self.c.dt_s/self.c.dy_m],
                "guard_m":self.c.guard_m,"horizon_s":self.horizon,"backtraces":rows,
                "proof":"Every innovation age lies between 0 and horizon. Linear backward characteristics attain extremes at endpoints; all crop edges stay inside the unwrapped rectangle. Internal advection is an exact permutation.",
                "limit":"Finite periodic embedding, not infinite-domain independence; required spatial/time covariance stencils must also remain below half-period in each coordinate."}


class CloudGRFSimulator:
    def __init__(self,c,embedding=None):
        self.c=c;self.embedding=embedding or CirculantGRF(c)
        for name in ("nx","ny","dx_m","dy_m","dt_s","slots","vx_m_s","vy_m_s","ell_c_m","guard_m","refine_x","refine_y","embedding_scale"):
            if getattr(c,name)!=getattr(self.embedding.c,name):
                raise ValueError("incompatible shared embedding")
        self.rng=np.random.Generator(np.random.PCG64(c.seed))
        self.field=self.embedding.draw(self.rng)
        self.slot=0
        self.initial=self.embedding.sample(self.field)
        self.theta=(float(ndtri(1-c.initial_fraction)) if c.threshold_mode=="ensemble" else
                    float(np.quantile(self.initial,1-c.initial_fraction)) if c.threshold_mode=="initial" else float(c.theta_c))

    def step(self):
        if self.slot>=self.c.slots-1:
            raise ValueError("configured horizon exhausted")
        self.field=self.c.rho*self.embedding.advect(self.field)+self.c.alpha*self.embedding.draw(self.rng)
        self.slot+=1
        return self.embedding.sample(self.field)


def relative_intensity(latent,theta,c):
    x=np.asarray(latent,dtype=float)
    if not np.isfinite(x).all() or not math.isfinite(theta):
        raise ValueError("finite latent and threshold required")
    with np.errstate(over="raise",invalid="raise"):
        result=c.A*np.maximum(0,x-theta)**c.q
    if not np.isfinite(result).all():
        raise ValueError("nonfinite intensity")
    return result


def components(mask):
    mask=np.asarray(mask)
    if mask.ndim!=2 or not np.isin(mask,[0,1]).all():
        raise ValueError("2D binary presence diagnostic required")
    return label(mask,structure=np.ones((3,3),dtype=int))


class DiagnosticTracker:
    """Observed 8-connected segments; ambiguous merges/splits terminate identity.

    Bilinear indicator weights are used ONLY for association, never for field
    advection. ROI/time censoring prevents calling observed spans physical lives.
    """
    def __init__(self,c):
        self.c=c;self.previous=None;self.active={};self.records=[];self.next_id=1

    def update(self,current,slot):
        count=int(current.max());prev=self.previous
        edges=set(np.unique(np.r_[current[0],current[-1],current[:,0],current[:,-1]]))-{0}
        pairs=[];old_degree=np.zeros(1,int);new_degree=np.zeros(count+1,int)
        if prev is not None:
            nold=int(prev.max());table=np.zeros((nold+1,count+1))
            sx=self.c.vx_m_s*self.c.dt_s/self.c.dx_m;sy=self.c.vy_m_s*self.c.dt_s/self.c.dy_m
            for oy in (math.floor(sy),math.floor(sy)+1):
                for ox in (math.floor(sx),math.floor(sx)+1):
                    weight=(1-abs(sy-oy))*(1-abs(sx-ox))
                    if weight<=0:continue
                    y0,y1=max(0,-oy),min(prev.shape[0],prev.shape[0]-oy)
                    x0,x1=max(0,-ox),min(prev.shape[1],prev.shape[1]-ox)
                    if y1<=y0 or x1<=x0:continue
                    a=prev[y0:y1,x0:x1];b=current[y0+oy:y1+oy,x0+ox:x1+ox]
                    table+=weight*np.bincount((a*(count+1)+b).ravel(),minlength=(nold+1)*(count+1)).reshape(table.shape)
            area_old=table.sum(axis=1);area_new=np.bincount(current.ravel(),minlength=count+1)
            overlap=table[1:,1:];union=area_old[1:,None]+area_new[None,1:]-overlap
            graph=(overlap>0)&(overlap/np.maximum(union,1e-100)>=self.c.tracking_iou)
            old_degree=np.r_[0,graph.sum(1)];new_degree=np.r_[0,graph.sum(0)]
            pairs=[(i+1,j+1) for i,j in zip(*np.where(graph)) if old_degree[i+1]==new_degree[j+1]==1]
        continued={j:self.active[i] for i,j in pairs}
        continued_old={i for i,j in pairs}
        ended=0
        for old_id,record in self.active.items():
            if old_id not in continued_old:
                reason="merge_split_or_ambiguous" if old_degree[old_id] else "disappeared_or_association_lost"
                self._end(record,reason,False);ended+=1
        active={}
        for j in range(1,count+1):
            if j in continued:
                record=continued[j]
            else:
                record={"track_id":self.next_id,"first_slot":slot,"last_slot":slot,
                        "left_time_censored":slot==0,"roi_censored":False,
                        "start_reason":"initial" if slot==0 else "merge_split_or_ambiguous" if new_degree[j] else "new_or_association_lost"}
                self.next_id+=1
            record["last_slot"]=slot;record["roi_censored"]|=j in edges
            active[j]=record
        self.active=active;self.previous=current.copy()
        return count-len(continued),ended

    def _end(self,record,reason,right):
        row=record.copy();row.update(end_reason=reason,right_time_censored=right,
                                    observed_span_s=(row["last_slot"]-row["first_slot"])*self.c.dt_s)
        self.records.append(row)

    def finish(self):
        for record in self.active.values():self._end(record,"simulation_end",True)
        self.active={}
        return self.records
