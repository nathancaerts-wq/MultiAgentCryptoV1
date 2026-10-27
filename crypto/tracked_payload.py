"""JSON-containers met mutation-versie, zonder wijziging van hun JSON-inhoud."""
from copy import deepcopy
from datetime import date,datetime,time,timedelta
from decimal import Decimal
from uuid import UUID

class Revision:
    def __init__(self): self.value=0;self.cacheable=True
    def changed(self): self.value+=1


def tracked(value, revision):
    if isinstance(value,dict):return TrackedDict(value,revision)
    if isinstance(value,list):return TrackedList(value,revision)
    if isinstance(value,tuple):return tuple(tracked(v,revision) for v in value)
    if not isinstance(value,(str,int,float,bool,type(None),Decimal,date,datetime,time,timedelta,UUID)):
        revision.cacheable=False
    return deepcopy(value)

class TrackedDict(dict):
    def __init__(self,values,revision):
        self._revision=revision
        dict.__init__(self,((k,tracked(v,revision)) for k,v in values.items()))
    def __deepcopy__(self,memo):return {deepcopy(k,memo):deepcopy(v,memo) for k,v in self.items()}
    def __setitem__(self,k,v):dict.__setitem__(self,k,tracked(v,self._revision));self._revision.changed()
    def __delitem__(self,k):dict.__delitem__(self,k);self._revision.changed()
    def clear(self):dict.clear(self);self._revision.changed()
    def pop(self,*args):
        value=dict.pop(self,*args);self._revision.changed();return value
    def popitem(self):
        value=dict.popitem(self);self._revision.changed();return value
    def setdefault(self,k,default=None):
        if k not in self:self[k]=default
        return self[k]
    def update(self,*args,**kw):
        for k,v in dict(*args,**kw).items():self[k]=v
    def __ior__(self,other):self.update(other);return self

class TrackedList(list):
    def __init__(self,values,revision):
        self._revision=revision;list.__init__(self,(tracked(v,revision) for v in values))
    def __deepcopy__(self,memo):return [deepcopy(v,memo) for v in self]
    def __setitem__(self,k,v):
        list.__setitem__(self,k,[tracked(x,self._revision) for x in v] if isinstance(k,slice) else tracked(v,self._revision));self._revision.changed()
    def __delitem__(self,k):list.__delitem__(self,k);self._revision.changed()
    def append(self,v):list.append(self,tracked(v,self._revision));self._revision.changed()
    def extend(self,vs):
        # Eerst materialiseren zodat extend(self) niet blijft groeien.
        values=[tracked(v,self._revision) for v in vs];list.extend(self,values);self._revision.changed()
    def insert(self,k,v):list.insert(self,k,tracked(v,self._revision));self._revision.changed()
    def pop(self,*args):
        v=list.pop(self,*args);self._revision.changed();return v
    def remove(self,v):list.remove(self,v);self._revision.changed()
    def clear(self):list.clear(self);self._revision.changed()
    def reverse(self):list.reverse(self);self._revision.changed()
    def sort(self,*args,**kw):
        try:list.sort(self,*args,**kw)
        finally:self._revision.changed()
    def __iadd__(self,other):self.extend(other);return self
    def __imul__(self,n):list.__imul__(self,n);self._revision.changed();return self
