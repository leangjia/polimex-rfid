from odoo import fields, models, api, _


class EmergencyGroup(models.Model):
    _name = 'hr.rfid.ctrl.emergency.group'
    _inherit = ['mail.thread', 'balloon.mixin']
    _description = 'Emergency signal distribution group'

    name = fields.Char(
        default='Emergency Floor 1'
    )
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)

    controller_ids = fields.One2many(
        comodel_name='hr.rfid.ctrl',
        inverse_name='emergency_group_id'
    )
    state = fields.Selection([
        ('normal', 'Normal'),
        ('emergency', 'Emergency')
    ],  compute='_compute_state',
        inverse='_inverse_state',
        tracking=True
    )

    @api.depends('controller_ids.emergency_state', 'controller_ids.input_states')
    def _compute_state(self):
        for g in self:
            g.state = any([c.emergency_state != 'off' for c in g.controller_ids]) and 'emergency' or 'normal'

    def _inverse_state(self):
        for g in self:
            if g.state == 'normal':
                ctrl_ids = g.controller_ids.filtered(lambda c: c.emergency_state == 'soft')
                ctrl_ids.emergency_state = 'off'
            if g.state == 'emergency':
                ctrl_ids = g.controller_ids.filtered(lambda c: c.emergency_state == 'off')
                ctrl_ids.emergency_state = 'soft'

    def emergency_on(self):
        for g in self:
            g.state = 'emergency'
        return self.balloon_success(
            title=_("The group turn on Emergency Mode Manually"),
            message=_("This will take time. For more information check controller's commands")
        )

    def emergency_off(self):
        for g in self:
            g.state = 'normal'
        return self.balloon_success(
            title=_("The group turn off Emergency Mode Manually"),
            message=_("This will take time. For more information check controller's commands")
        )
