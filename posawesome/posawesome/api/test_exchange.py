import importlib.util
import json
import pathlib
import sys
import types
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_ORIGINAL_MODULES = dict(sys.modules)


def tearDownModule():
    for name in list(sys.modules):
        if name.startswith(("frappe", "posawesome")) and name not in _ORIGINAL_MODULES:
            sys.modules.pop(name, None)
    for name, module in _ORIGINAL_MODULES.items():
        if name.startswith(("frappe", "posawesome")):
            sys.modules[name] = module


class AttrDict(dict):
    __getattr__ = dict.get


def _load_exchange_module():
    frappe = types.ModuleType("frappe")
    frappe._ = lambda text: text
    frappe._dict = lambda value=None: AttrDict(value or {})
    frappe.parse_json = json.loads
    frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe.throw = lambda message, *args, **kwargs: (_ for _ in ()).throw(ValueError(message))
    frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: False)
    sys.modules["frappe"] = frappe

    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.cint = lambda value: int(value or 0)
    frappe_utils.cstr = lambda value: "" if value is None else str(value)
    frappe_utils.flt = lambda value, *_args, **_kwargs: float(value or 0)
    sys.modules["frappe.utils"] = frappe_utils

    creation = types.ModuleType("posawesome.posawesome.api.invoice_processing.creation")
    creation.submit_invoice = lambda *args, **kwargs: None
    sys.modules[creation.__name__] = creation

    pos_access = types.ModuleType("posawesome.posawesome.api.pos_access")
    pos_access.get_authorized_pos_profile = lambda *args, **kwargs: None
    sys.modules[pos_access.__name__] = pos_access

    module_name = "posawesome.posawesome.api.exchange"
    module_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "exchange.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestExchangeValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exchange = _load_exchange_module()

    def setUp(self):
        self.profile = AttrDict(
            name="Main POS",
            company="Example Co",
            posa_allow_return=1,
            posa_allow_item_exchange=1,
            create_pos_invoice_instead_of_sales_invoice=0,
        )
        self.return_invoice = AttrDict(
            doctype="Sales Invoice",
            company="Example Co",
            pos_profile="Main POS",
            customer="Customer A",
            currency="PKR",
            is_return=1,
            return_against="SINV-0001",
            items=[{"item_code": "OLD", "qty": -1}],
            payments=[{"amount": 0}],
        )
        self.sale_invoice = AttrDict(
            doctype="Sales Invoice",
            company="Example Co",
            pos_profile="Main POS",
            customer="Customer A",
            currency="PKR",
            is_return=0,
            items=[{"item_code": "NEW", "qty": 1}],
            payments=[{"amount": 500}],
        )

    def test_accepts_linked_sales_invoice_exchange(self):
        self.exchange._validate_exchange_payload(
            self.return_invoice,
            self.sale_invoice,
            self.profile,
        )

    def test_rejects_cross_customer_exchange(self):
        self.sale_invoice["customer"] = "Customer B"
        with self.assertRaisesRegex(ValueError, "same customer"):
            self.exchange._validate_exchange_payload(
                self.return_invoice,
                self.sale_invoice,
                self.profile,
            )

    def test_rejects_cash_refund_inside_return_credit(self):
        self.return_invoice["payments"] = [{"amount": -100}]
        with self.assertRaisesRegex(ValueError, "direct cash refund"):
            self.exchange._validate_exchange_payload(
                self.return_invoice,
                self.sale_invoice,
                self.profile,
            )

    def test_rejects_exchange_when_returns_are_disabled(self):
        self.profile["posa_allow_return"] = 0
        with self.assertRaisesRegex(ValueError, "Returns are not enabled"):
            self.exchange._validate_exchange_payload(
                self.return_invoice,
                self.sale_invoice,
                self.profile,
            )

    def test_rejects_pos_invoice_mode_until_reconciliation_is_supported(self):
        self.profile["create_pos_invoice_instead_of_sales_invoice"] = 1
        with self.assertRaisesRegex(ValueError, "requires the POS Profile to create Sales Invoices"):
            self.exchange._validate_exchange_payload(
                self.return_invoice,
                self.sale_invoice,
                self.profile,
            )

    def test_accepts_fully_closed_exchange_settlement(self):
        return_doc = AttrDict(outstanding_amount=0)
        sale_doc = AttrDict(outstanding_amount=0)
        self.exchange._validate_final_settlement(return_doc, sale_doc, 1500, 1600)

    def test_accepts_remaining_customer_credit(self):
        return_doc = AttrDict(outstanding_amount=-400)
        sale_doc = AttrDict(outstanding_amount=0)
        self.exchange._validate_final_settlement(return_doc, sale_doc, 2000, 1600)

    def test_rejects_unpaid_replacement_difference(self):
        return_doc = AttrDict(outstanding_amount=0)
        sale_doc = AttrDict(outstanding_amount=100)
        with self.assertRaisesRegex(ValueError, "did not close correctly"):
            self.exchange._validate_final_settlement(return_doc, sale_doc, 1500, 1600)


if __name__ == "__main__":
    unittest.main()
