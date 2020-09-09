'''
Weight data (manually logged)
'''

from datetime import datetime
from typing import NamedTuple, Iterator

from ..core import LazyLogger
from ..core.error import Res, set_error_datetime, extract_error_datetime

from ..notes import orgmode

from my.config import weight as config


log = LazyLogger('my.body.weight')


class Entry(NamedTuple):
    dt: datetime
    value: float
    # TODO comment??


Result = Res[Entry]


# TODO cachew? but in order for that to work, would need timestamps for input org-mode files..
def from_orgmode() -> Iterator[Result]:
    orgs = orgmode.query()
    for o in orgs.query_all(lambda o: o.with_tag('weight')):
        try:
            # TODO can it throw? not sure
            created = o.created
            assert created is not None
        except Exception as e:
            log.exception(e)
            yield e
            continue
        try:
            w = float(o.heading)
        except Exception as e:
            set_error_datetime(e, dt=created)
            log.exception(e)
            yield e
            continue
        # todo perhaps, better to use timezone provider
        created = config.default_timezone.localize(created)
        yield Entry(
            dt=created,
            value=w,
            # TODO add org note content as comment?
        )


def dataframe():
    import pandas as pd # type: ignore
    entries = from_orgmode()
    def it():
        for e in from_orgmode():
            if isinstance(e, Exception):
                dt = extract_error_datetime(e)
                yield {
                    'dt'    : dt,
                    'error': str(e),
                }
            else:
                yield {
                    'dt'    : e.dt,
                    'weight': e.value,
                }
    df = pd.DataFrame(it())
    df.set_index('dt', inplace=True)
    # TODO not sure about UTC??
    df.index = pd.to_datetime(df.index, utc=True)
    return df

# TODO move to a submodule? e.g. my.body.weight.orgmode?
# so there could be more sources
# not sure about my.body thing though
