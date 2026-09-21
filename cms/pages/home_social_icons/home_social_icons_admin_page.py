"""
cms/pages/home_social_icons/home_social_icons_admin_page.py

Intentionally still a stub — DO NOT build a Page Object here before reading
this. See `cms/tests/home_social_icons/test_home_social_icons_control_panel.py`'s
module docstring for the full explanation:

The CMS Object Authoring surface this page/PBI needs (`manage-social-media-
icon`) already has a real, live-verified Page Object —
`SocialMediaIconAdminPage` in `cms/pages/components/footer_admin_component.py`
— built for PBI 129366/129373's shared "Social Media Icons" surface (one
CMS object, confirmed live to serve both the site footer and the Home-page
"Find us on social media" widget; see that module's "LOAD-BEARING FINDING
#1"). All 29 of this PBI's ADO cases (131168-131196) are already scripted
against it in `cms/tests/components/test_footer_control_panel.py`.

Creating a second Page Object here for the same live surface would duplicate
locators/methods the redundancy scan explicitly forbids ("no duplicated
locator constants for the same element across objects; no copy-pasted
Page-Object methods that should be a shared component object"). Whether this
surface's automation should physically live under `home_social_icons/`
instead of `pages/components/` (per `.claude/context/active/standards.md`'s
Automation Structure table mapping QC-HOME-004B -> file base
`home_social_icons`) is flagged as an open placement question for the QA
Manager, not resolved by moving files in this pass.
"""
