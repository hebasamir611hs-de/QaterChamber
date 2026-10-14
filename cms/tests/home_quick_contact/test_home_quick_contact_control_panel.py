"""
cms/tests/home_quick_contact/test_home_quick_contact_control_panel.py — PBI 129390.

2026-10-08 (Phase 3, B-129390): the two Control_Panel cases that lived here
(ADO-136480, ADO-136551) were permanently skipped behind TODO-placeholder
locators and a TEST_USER-only login. They are now real tests in
`cms/tests/home_contact_us/test_home_contact_us_control_panel.py`
(`test_management_screen_renders_all_configuration_fields_136480`,
`test_management_screen_renders_in_arabic_136551`), next to every other
Control_Panel case of this PBI. Nothing is collected from this module.
"""
