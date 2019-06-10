import numpy as np

def adv_make_campaign(demand_shape,cycle_length=100,min_max=(0,100),
                      variability=0.,n_cycles=1,mission_type=None,mission_ratio=None):
    ''' Makes a campaign specification for mission generation in "campaign" format '''
    
    min_max_ = [min_max[0]+variability,min_max[1]-variability]
    if isinstance(demand_shape, list):
        y = demand_shape
    elif demand_shape in ['sine','square']:
        t = np.arange(cycle_length)
        f = 1./float(cycle_length)
        s = 2*np.pi*(f*t)
        y = np.sin(s)
        if demand_shape is 'sine':
            y = 0.5*(y+1)
        elif demand_shape is 'square':
            y = ((y>=0) * 1 + (s<0)*0)
        y = (min_max_[1]-min_max_[0])*y + min_max_[0]
    elif demand_shape is 'triangle':
        t = np.arange(cycle_length)
        a = 0.5*float(cycle_length)
        y = (t/a-np.floor(t/a+0.5))*(-1)**np.floor(t/a+0.5)+0.5
        y = (min_max_[1]-min_max_[0])*y + min_max_[0]
    elif demand_shape is 'sawtooth':
        t = np.arange(cycle_length)
        a = float(cycle_length)
        y = (t/a-np.floor(t/a))
        y = (min_max_[1]-min_max_[0])*y + min_max_[0]
    else:
        y = [min_max_[1]]*cycle_length
    
    # Convert to np array
    y = np.array(y)
    
    # repeat n_cycles
    y = np.tile(y, n_cycles)
    
    # Add variability
    if variability > 0:
        y += np.random.normal(0,variability,len(y))
    
    # anything less than 0 is 0
    y[y<min_max[0]] = min_max[0]
    y[y>min_max[1]] = min_max[1]

    # convert to list  
    y = np.round(y)
    y = np.array(y,dtype=np.int)

    # make output
    myOut = {}
    myOut['campaign'] = []
    sorties_defn = {}
    if mission_type:
        sorties_defn['mission_type']=mission_type
    if mission_ratio:
        sorties_defn['mission_ratio']=mission_ratio
    if len(sorties_defn) > 0:
        myOut['campaign'] = [(1,x,sorties_defn) for x in y]
    else:
        myOut['campaign'] = [(1,x) for x in y]
    return myOut