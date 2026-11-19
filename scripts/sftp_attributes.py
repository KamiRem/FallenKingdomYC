"""Attributs SFTP observés, sans confondre absence et zéro."""
import stat

def capture(item):
    names={'size':('st_size',1),'mtime':('st_mtime',8),'mode':('st_mode',4),'uid':('st_uid',2),'gid':('st_gid',2)}
    flags=getattr(item,'_flags',None)
    result={'wireFlags':flags,'attributes':{}}
    for field,(attribute,mask) in names.items():
        value=getattr(item,attribute,None)
        declared=None if flags is None else bool(flags&mask)
        available=value is not None and declared is not False
        result['attributes'][field]={'value':(stat.S_IMODE(value) if field=='mode' and value is not None else value),'available':available,'pythonAttributePresent':hasattr(item,attribute),'wireDeclared':declared}
    raw=getattr(item,'st_mode',None)
    kind=stat.S_IFMT(raw) if raw is not None else None
    result['rawMode']=raw;result['rawModeOctal']=oct(raw) if raw is not None else None
    result['attributes']['type']={'value':kind,'available':result['attributes']['mode']['available'] and kind not in (None,0),'label':{stat.S_IFREG:'regular',stat.S_IFDIR:'directory',stat.S_IFLNK:'symlink',0:'unspecified',None:'absent'}.get(kind,'special')}
    return result

CRITICAL=('type','size','mtime','mode')
OPTIONAL=('uid','gid')
def compare(expected,observed,*,same_source=False):
    """Les champs non comparables sont explicitement non vérifiés, jamais égaux."""
    result={'verifiedFields':[],'unverifiedFields':[],'differences':[],'missingCritical':[],'availabilityLost':[],'optionalStatus':{}}
    for field in CRITICAL+OPTIONAL:
        a=expected['attributes'][field];b=observed['attributes'][field]
        if not a['available'] or not b['available']:
            result['unverifiedFields'].append(field)
            if field in CRITICAL:result['missingCritical'].append(field)
            else:
                result['optionalStatus'][field]=('both_absent_not_verified' if not a['available'] and not b['available'] else 'expected_absent_not_comparable' if not a['available'] else 'observed_absent_not_comparable')
                if same_source and a['available'] and not b['available']:result['availabilityLost'].append(field)
        elif a['value']!=b['value']:
            result['differences'].append(field)
            if field in OPTIONAL:result['optionalStatus'][field]='different'
        else:
            result['verifiedFields'].append(field)
            if field in OPTIONAL:result['optionalStatus'][field]='verified_equal'
    result['criticalVerified']=not result['missingCritical'] and not any(x in CRITICAL for x in result['differences'])
    result['fullyComparable']=not result['unverifiedFields']
    result['accepted']=not(result['differences'] or result['missingCritical'] or result['availabilityLost'])
    return result
