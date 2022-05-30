# -*- coding: utf-8 -*-
from odoo import models, api, fields, _, exceptions


class HrRfidZone(models.Model):
    _inherit = 'hr.rfid.zone'

    attendance = fields.Boolean(
        string='Attendance',
        help='Zone will track attendance if ticked.',
        default=False,
    )

    overwrite_check_in = fields.Boolean(
        string='Overwrite check-in',
        help='If a the user has already checked in and also enters this zone then overwrite the time of the check in',
        default=False,
    )

    overwrite_check_out = fields.Boolean(
        string='Overwrite check-out',
        help='If a the user has already checked out and also leaves this zone then overwrite the time of the check out',
        default=False,
    )

    max_time_in_zone = fields.Float(
        help='Maximum attendance time in zone. Used for auto-close attendance. Zero means not use.',
        default=12,
        digits=(2, 2)
    )
    auto_close_time_for_zone = fields.Float(
        help='Attendance time in zone if autoclosed. Used for auto-close attendance',
        default=7,
        digits=(2, 2)
    )
    delete_attendance_if_late_more_than = fields.Float(
        help='Remove attendance for employee if late is more than this time. Set zeo to disable function.',
        default=0,
        digits=(2, 2)
    )

    def person_entered(self, person, event):
        if not isinstance(person, type(self.env['hr.employee'])):
            return super(HrRfidZone, self).person_entered(person, event)

        for zone in self:
            if zone.attendance is False:
                continue

            if person.attendance_state == 'checked_in' and zone.overwrite_check_in:
                event.in_or_out = 'in'
                person.check_in = event.event_time
            elif person.attendance_state == 'checked_out':
                event.in_or_out = 'in'
                person.attendance_action_change_with_date(event.event_time, zone.id)
        return super(HrRfidZone, self).person_entered(person, event)

    def person_left(self, person, event=None):
        if not isinstance(person, type(self.env['hr.employee'])):
            return super(HrRfidZone, self).person_left(person, event)

        for zone in self.filtered(lambda z: z.attendance and event):
            if person.attendance_state == 'checked_out' and zone.overwrite_check_out:
                check = self.env['hr.attendance'].search([('employee_id', '=', person.id)], limit=1)
                if event:
                    event.in_or_out = 'out'
                    check.check_out = event.event_time
                else:
                    check.check_out = fields.datetime.now()
            elif person.attendance_state == 'checked_in':
                if event:
                    event.in_or_out = 'out'
                    person.attendance_action_change_with_date(event.event_time, zone.id)
                else:
                    person.attendance_action_change_with_date(fields.datetime.now(), zone.id)

        return super(HrRfidZone, self).person_left(person, event)

    def attendance_for_current_zone(self):
        self.ensure_one()
        return {
            'name': _("Check In's {}").format(self.name),
            'view_mode': 'tree,form',
            'res_model': 'hr.attendance',
            'domain': [('id', 'in', [i.id for i in self.employee_ids])],
            'type': 'ir.actions.act_window',
            # 'help': _('''<p class="o_view_nocontent">
            #         Buy Odoo Enterprise now to get more providers.
            #     </p>'''),
        }
