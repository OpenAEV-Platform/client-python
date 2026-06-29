import unittest
from unittest.mock import MagicMock, sentinel

import pyoaev.base as module


class TestRESTObject(unittest.TestCase):
    def test_restobject_minimal_init(self):
        manager = MagicMock()
        manager.parent_attrs = {"parentkey1": "parentvalue1"}
        attrs = {"key1": "value1"}
        created_from_list = sentinel._created_from_list

        rest_object = module.RESTObject(manager, attrs, created_from_list=created_from_list)

        self.assertEqual(rest_object.manager, manager)
        self.assertEqual(rest_object._attrs, attrs)
        self.assertEqual(rest_object._created_from_list, created_from_list)
        self.assertEqual(rest_object._updated_attrs, {})
        self.assertEqual(rest_object._parent_attrs, manager.parent_attrs)
        self.assertEqual(str(rest_object), "<class 'pyoaev.base.RESTObject'> => {'key1': 'value1'}")

        # properties
        self.assertEqual(rest_object.attributes, {"key1": "value1", "parentkey1": "parentvalue1"})
        self.assertIsNone(rest_object.encoded_id)

    def test_restobject_failed_init(self):
        manager = MagicMock()
        attrs = MagicMock()
        created_from_list = sentinel._created_from_list

        with self.assertRaises(module.OpenAEVParsingError):
            module.RESTObject(manager, attrs, created_from_list=created_from_list)

    def test_restobject_to_json(self):
        manager = MagicMock()
        manager.parent_attrs = {"parentkey1": "parentvalue1"}
        attrs = {"key1": "value1"}
        created_from_list = sentinel._created_from_list

        rest_object = module.RESTObject(manager, attrs, created_from_list=created_from_list)

        jsondata = rest_object.to_json()

        self.assertEqual(
            jsondata,
            '{"key1": "value1"}'
        )
        self.assertNotIn("parentkey1", jsondata)

    def test_restobject_get_id(self):
        manager = MagicMock()
        manager.parent_attrs = {"parentkey1": "parentvalue1"}
        attrs = {"key1": "value1"}
        created_from_list = sentinel._created_from_list

        rest_object = module.RESTObject(manager, attrs, created_from_list=created_from_list)

        self.assertIsNone(rest_object.get_id())

        rest_object._update_attrs({"_id_attr": "my_id"})

        self.assertIsNone(rest_object.get_id())
