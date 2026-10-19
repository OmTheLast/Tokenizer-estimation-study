import unittest
from decimal import Decimal
from prepare_published_inputs import exact_loads, exact_dumps, fingerprint


class ExactJSON(unittest.TestCase):
    def test_nested_values_and_order_and_precision(self):
        text = '{"z":123456789012345678901234567890,"a":[-0,0.123456789012345678901,1.200e-80,true,false,null,"தமிழ்\\n\\\"x"],"empty":{},"list":[]}'
        value = exact_loads(text)
        for pretty in (False, True):
            encoded = exact_dumps(value, pretty)
            self.assertEqual(fingerprint(value), fingerprint(exact_loads(encoded)))
            self.assertFalse(encoded.endswith('\n'))
            self.assertLess(encoded.index('"z"'), encoded.index('"a"'))
        self.assertEqual(value['a'][0].as_tuple().sign, 1)

    def test_layout_differs_only_outside_strings(self):
        value = exact_loads('{"a":"  spaced \\t text  ","b":[1,{"x":2}]}')
        compact, pretty = exact_dumps(value), exact_dumps(value, True)
        def remove_outer_whitespace(s):
            quoted = escaped = False; out = []
            for c in s:
                if quoted or not c.isspace(): out.append(c)
                if escaped: escaped = False
                elif quoted and c == '\\': escaped = True
                elif c == '"': quoted = not quoted
            return ''.join(out)
        self.assertEqual(remove_outer_whitespace(pretty), compact)
        self.assertIn('\n  "a": ', pretty)

    def test_invalid_numbers_and_duplicate_keys(self):
        for text in ('{"x":NaN}', '{"x":Infinity}', '{"x":1,"x":2}', '{"x":{"y":1,"y":2}}'):
            with self.assertRaises(ValueError): exact_loads(text)
        with self.assertRaises(ValueError): exact_dumps(Decimal('NaN'))
        with self.assertRaises(TypeError): exact_dumps(1.25)


if __name__ == '__main__': unittest.main()
