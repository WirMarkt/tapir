from django import template
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import FinancingCampaign
from tapir.core.models import SidebarLinkGroup
from tapir.shifts.templatetags.shifts import get_current_week_group

register = template.Library()


@register.inclusion_tag("core/sidebar_links.html", takes_context=True)
def sidebar_links(context):
    groups = get_sidebar_link_groups(context["request"])

    for group in groups:
        for link in group.links:
            link["is_active"] = link["url"] == context["request"].path

    context["sidebar_link_groups"] = groups

    return context


def get_sidebar_link_groups(request):
    groups = []

    if request.user.has_perm("coop.manage"):
        coop_group = SidebarLinkGroup(name=_("Cooperative"))
        coop_group.add_link(
            display_name=_("Applicants"),
            material_icon="person_outline",
            url=reverse_lazy("coop:draftuser_list"),
        )
        coop_group.add_link(
            display_name=_("Members"),
            material_icon="person",
            url=reverse_lazy("coop:shareowner_list"),
        )
        coop_group.add_link(
            display_name=_("Matching program"),
            material_icon="card_giftcard",
            url=reverse_lazy("coop:matching_program_list"),
        )
        coop_group.add_link(
            display_name=_("Incoming payments"),
            material_icon="euro",
            url=reverse_lazy("coop:incoming_payment_list"),
        )
        groups.append(coop_group)

    if request.user.has_perm("welcomedesk.view"):
        welcomedesk_group = SidebarLinkGroup(name=_("Welcome Desk"))
        welcomedesk_group.add_link(
            display_name=_("Welcome Desk"),
            material_icon="table_restaurant",
            url=reverse_lazy("coop:welcome_desk_search"),
            html_id="welcome_desk_link",
        )
        groups.append(welcomedesk_group)

    current_week_group_name = "???"
    current_week_group = get_current_week_group()
    if current_week_group is not None:
        current_week_group_name = current_week_group.name

    shifts_group = SidebarLinkGroup(name=_("Shifts"))
    groups.append(shifts_group)
    shifts_group.add_link(
        display_name=_("Shift calendar"),
        material_icon="calendar_today",
        url=reverse_lazy("shifts:calendar_future"),
    )
    shifts_group.add_link(
        display_name=_("ABCD-shifts week-plan"),
        material_icon="today",
        url=reverse_lazy("shifts:shift_template_overview"),
    )
    shifts_group.add_link(
        display_name=_(
            "ABCD annual calendar, current week: {current_week_group_name}"
        ).format(current_week_group_name=current_week_group_name),
        material_icon="table_view",
        url=reverse_lazy("shifts:shift_template_group_calendar"),
    )

    if request.user.has_perm("shifts.manage"):
        shifts_group.add_link(
            display_name=_("Past shifts"),
            material_icon="history",
            url=reverse_lazy("shifts:calendar_past"),
        )
        shifts_group.add_link(
            display_name=_("Shift exemptions"),
            material_icon="beach_access",
            url=reverse_lazy("shifts:shift_exemption_list"),
        )
        shifts_group.add_link(
            display_name=_("Members on alert"),
            material_icon="priority_high",
            url=reverse_lazy("shifts:members_on_alert"),
        )
        shifts_group.add_link(
            display_name=_("Add a shift"),
            material_icon="add_circle_outline",
            url=reverse_lazy("shifts:create_shift"),
        )

    if request.user.has_perm("shifts.manage") and FinancingCampaign.objects.exists():
        campaign_group = SidebarLinkGroup(name=_("Financing campaign"))
        groups.append(campaign_group)
        for campaign in FinancingCampaign.objects.all():
            campaign_group.add_link(
                display_name=_(campaign.name),
                material_icon="euro",
                url=campaign.get_absolute_url(),
            )

    misc_group = SidebarLinkGroup(name=_("Miscellaneous"))
    groups.append(misc_group)
    misc_group.add_link(
        display_name=_("Website"),
        material_icon="public",
        url="https://wirmarkt.de",
    )
    misc_group.add_link(
        display_name=_("Chat"),
        material_icon="chat",
        url=reverse_lazy("coop:tools_chat"),
    )
    misc_group.add_link(
        display_name=_("App"),
        material_icon="smartphone",
        url=reverse_lazy("coop:tools_app"),
    )
    # misc_group.add_link(
    #     display_name=_("Member manual"),
    #     material_icon="menu_book",
    #     url="https://wirmarkt.de",
    # )
    # misc_group.add_link(
    #     display_name=_("Shop opening hours"),
    #     material_icon="access_time",
    #     url="https://wirmarkt.de",
    # )
    misc_group.add_link(
        display_name=_("Contact the member office"),
        material_icon="email",
        url="mailto:office@wirmarkt.de.de",
    )
    misc_group.add_link(
        display_name=_("Coop statistics"),
        material_icon="calculate",
        url=reverse_lazy("coop:statistics"),
    )
    misc_group.add_link(
        display_name=_("Shift statistics"),
        material_icon="calculate",
        url=reverse_lazy("shifts:statistics"),
    )
    misc_group.add_link(
        display_name=_("About tapir"),
        material_icon="help",
        url=reverse_lazy("coop:about"),
    )

    return groups
