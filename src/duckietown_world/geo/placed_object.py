# coding=utf-8
from __future__ import unicode_literals


__all__ = ['PlacedObject']

from duckietown_serialization_ds1 import Serializable

import copy


class SpatialRelation(Serializable):
    SR_TYPE_PRIOR = 'prior'
    SR_TYPE_GT = 'ground_truth'
    SR_TYPE_MEASUREMENT = 'measurement'
    SR_TYPES = [SR_TYPE_PRIOR, SR_TYPE_GT, SR_TYPE_MEASUREMENT]

    def __init__(self, a, transform, b, sr_type):
        # check_isinstance(transform, (SpatialRelation, Sequence))
        if sr_type not in SpatialRelation.SR_TYPES:
            msg = 'Invalid value %s' % sr_type
            raise ValueError(msg)
        self.a = tuple(a)
        self.transform = transform
        self.b = tuple(b)
        self.sr_type = sr_type

    def filter_all(self, f):
        return SpatialRelation(self.a, f(self.transform), self.b, sr_type=self.sr_type)

    def params_from_json_dict(self, d):
        a = d.pop('a', [])
        b = d.pop('b')
        sr_type = d.pop('sr_type')
        transform = d.pop('transform')

        return dict(a=a,b=b,sr_type=sr_type, transform=transform)

    def params_to_json_dict(self):
        res = {}
        if self.a:
            res['a'] = list(self.a)
        res['b'] = self.b
        res['sr_type'] = self.sr_type
        return res

class PlacedObject(Serializable):
    def __init__(self, children=None, spatial_relations=None):
        # name of the frame to Transform object
        if children is None:
            children = {}

        if spatial_relations is None:
            spatial_relations = {}

        self.children = children

        for k, v in list(spatial_relations.items()):
            from .transforms import Transform
            if isinstance(v, Transform):
                if k in self.children:
                    sr = SpatialRelation(a=(), b=(k,), sr_type='ground_truth',
                                         transform=v)
                    spatial_relations[k] = sr
                else:
                    msg = 'What is the "%s" referring to?' % k
                    raise ValueError(msg)

        self.spatial_relations = spatial_relations

        if not spatial_relations:
            for child in self.children:
                from duckietown_world import SE2Transform
                sr = SpatialRelation(a=(), b=(child,), sr_type='ground_truth',
                                     transform=SE2Transform.identity())
                self.spatial_relations[child] = sr


        # self.children = MyDict(**children)
        # self.spatial_relations = MyDict(**spatial_relations)

    def filter_all(self, f):
        x = copy.deepcopy(self)

        x.children = dict((k, f(v.filter_all(f))) for (k, v) in self.children.items())
        x.spatial_relations = dict((k, f(v.filter_all(f))) for (k, v) in self.spatial_relations.items())
        return x
        # klass = type(self)
        # params = self.params_to_json_dict()
        # return f(klass(**params))

    def get_object_from_fqn(self, fqn):
        if fqn == ():
            return self
        first, rest = fqn[0], fqn[1:]
        if first in self.children:
            return self.children[first].get_object_from_fqn(rest)
        else:
            msg = 'Cannot find child %s in %s' % (first, list(self.children))
            raise KeyError(msg)

    def params_to_json_dict(self):
        res = {}

        if self.children:
            res['children'] = self.children
        if self.spatial_relations:
            res['spatial_relations'] = self.spatial_relations

        return res

    def set_object(self, name, ob, **transforms):
        assert self is not ob
        self.children[name] = ob
        for k, v in transforms.items():
            st = SpatialRelation(a=(), b=(name,), sr_type=k, transform=v)
            i = len(self.spatial_relations)
            self.spatial_relations[i] = st

    # @abstractmethod
    def draw_svg(self, drawing, g):
        from duckietown_world.world_duckietown.duckiebot import draw_axes
        draw_axes(drawing, g)

        # print('draw_svg not implemented for %s' % type(self).__name__)

    def get_drawing_children(self):
        return sorted(self.children)

    def extent_points(self):
        return [(0.0, 0.1), (0.1, 0.0)]
