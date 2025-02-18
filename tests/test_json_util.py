import datetime

import pytest

from testsuite.utils import json_util

NOW = datetime.datetime(2019, 9, 19, 13, 4)


@pytest.mark.parametrize(
    'json_input',
    [
        ({'$timeDelta': 60}),
        ({'$mockserver': '/path'}),
        ({'$date': '2020-01-01'}),
    ],
)
def test_substitute_hook_disabled(json_input):
    result = json_util.substitute(json_input, object_hook=None)
    assert result == json_input


@pytest.mark.parametrize(
    'json_input,expected_result',
    [
        ({'$timeDelta': 60}, '<time-delta>'),
        ({'$mockserver': '/path'}, '<unexpected>'),
        ({'$date': '2020-01-01'}, '<unexpected>'),
        ({'$myVar': 'value'}, '<my-var-value>'),
    ],
)
def test_substitute_custom_hook(json_input, expected_result):
    def _my_obj_hook(doc: dict):
        if '$timeDelta' in doc:
            return '<time-delta>'
        if '$myVar' in doc:
            return '<my-var-%s>' % doc['$myVar']
        return '<unexpected>'

    result = json_util.substitute(json_input, object_hook=_my_obj_hook)
    assert result == expected_result


@pytest.mark.parametrize(
    'json_input,expected_result',
    [
        (  # simple list
            [{'some_date': {'$dateDiff': 0}}, 'regular_element'],  # json_input
            [{'some_date': NOW}, 'regular_element'],  # expected_result
        ),
        (  # simple dict
            {  # json_input
                'some_date': {'$dateDiff': 0},
                'regular_key': 'regular_value',
            },
            {'some_date': NOW, 'regular_key': 'regular_value'},  # json_input
        ),
        (  # nested list and dict
            {  # json_input
                'regular_root_key': 'regular_root_value',
                'root_date': {'$dateDiff': 0},
                'parent_key': {
                    'nested_date': {'$dateDiff': 0},
                    'nested_list': [
                        'regular_element1',
                        {'$dateDiff': 0},
                        {'$dateDiff': 0},
                        'regular_element2',
                    ],
                },
            },
            {  # expected_result
                'regular_root_key': 'regular_root_value',
                'root_date': NOW,
                'parent_key': {
                    'nested_date': NOW,
                    'nested_list': [
                        'regular_element1',
                        NOW,
                        NOW,
                        'regular_element2',
                    ],
                },
            },
        ),
    ],
)
@pytest.mark.now('2019-09-19 13:04:00')
def test_substitute_now(object_hook, json_input, expected_result):
    result = json_util.substitute(json_input, object_hook=object_hook)
    assert result == expected_result


@pytest.mark.parametrize(
    'json_input,expected_result',
    [
        ({'$timeDelta': 60}, datetime.timedelta(seconds=60)),
        ({'$timeDelta': '1e-6'}, datetime.timedelta(microseconds=1)),
        ({'$timeDelta': -0.5}, -(datetime.timedelta(milliseconds=500))),
    ],
)
def test_substitute_timedelta(object_hook, json_input, expected_result):
    result = json_util.substitute(json_input, object_hook=object_hook)
    assert result == expected_result


@pytest.mark.parametrize(
    'json_input,expected_result',
    [
        ({'$myObjHook': 'any-string'}, '<my-custom-obj>'),
        ({'key': {'$myObjHook': 'any-string'}}, {'key': '<my-custom-obj>'}),
    ],
)
def test_substitute_with_custom_hook(object_hook, json_input, expected_result):
    result = json_util.substitute(json_input, object_hook=object_hook)
    assert result == expected_result


@pytest.mark.parametrize(
    'json_input,expected_result',
    [
        ({'$match': 'any-string'}, 'any string matches'),
        ({'$match': {'type': 'any-string'}}, 'other string matches'),
        ({'$match': {'type': 'regex', 'pattern': '^[0-9]{2}$'}}, '38'),
        ({'$match': {'type': 'custom-matching'}}, '<my-custom-type>'),
    ],
)
def test_substitute_with_matching(object_hook, json_input, expected_result):
    result = json_util.substitute(json_input, object_hook=object_hook)
    assert result == expected_result
