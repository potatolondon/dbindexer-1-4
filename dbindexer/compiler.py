from .resolver import resolver
from django.utils.importlib import import_module

def __repr__(self):
    return '<%s, %s, %s, %s>' % (self.alias, self.col, self.field.name,
        self.field.model.__name__)

from django.db.models.sql.where import Constraint
Constraint.__repr__ = __repr__

# TODO: manipulate a copy of the query instead of the query itself. This has to
# be done because the query can be reused afterwards by the user so that a
# manipulated query can result in strange behavior for these cases!
# TODO: Add watching layer which gives suggestions for indexes via query inspection
# at runtime

class BaseCompiler(object):
    def convert_filters(self):
        resolver.convert_filters(self.query)

class SQLCompiler(BaseCompiler):
    def execute_sql(self, *args, **kwargs):
        self.convert_filters()
        return super(SQLCompiler, self).execute_sql(*args, **kwargs)

    def results_iter(self):
        self.convert_filters()
        return super(SQLCompiler, self).results_iter()

    def has_results(self):
        self.convert_filters()
        return super(SQLCompiler, self).has_results()


class SQLInsertCompiler(BaseCompiler):
    def execute_sql(self, return_id=False):
        # This is a bit hacky. execute_sql in the parent class
        # is responsible for calling pre_save unless the query
        # is a raw query. We need pre_save to be called so that
        # auto_now type fields are populated. So we call pre_save
        # ourselves, and mark the query as raw so pre_save isn't called
        # twice, then we set it back to its original value

        for obj in self.query.objs:
            for field in self.query.fields:
                if not field.rel: #Don't do anything to related objects
                    setattr(obj, field.name, field.pre_save(obj, obj._state.adding))

        original_state = self.query.raw
        self.query.raw = True

        resolver.convert_insert_query(self.query)
        result = super(SQLInsertCompiler, self).execute_sql(return_id=return_id)

        if self.query.raw != original_state:
            self.query.raw = original_state
        return result

class SQLUpdateCompiler(BaseCompiler):
    pass

class SQLDeleteCompiler(BaseCompiler):
    pass
