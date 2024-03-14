# -*- coding: utf-8 -*-



import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LaundryManagement(models.Model):
    _name = 'laundry.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Laundry Order"
    _order = 'order_date desc, id desc'
    
    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('laundry.order')
    #     return super(LaundryManagement, self).create(vals)
    
    @api.depends('order_lines')
    def get_total(self):
        total = 0
        for obj in self:
            for each in obj.order_lines:
                total += each.amount
            obj.total_amount = total
    
    # def confirm_order(self):
    #     self.state = 'order'
    #     sale_obj = self.env['sale.order'].create(
    #         {'partner_id': self.partner_id.id,
    #          'partner_invoice_id': self.partner_invoice_id.id,
    #          'partner_shipping_id': self.partner_shipping_id.id})
    #     self.sale_obj = sale_obj
    #     product_id = self.env.ref('laundry_management.laundry_service')
    #     self.env['sale.order.line'].create({'product_id': product_id.id,
    #                                         'name': 'Laundry Service',
    #                                         'price_unit': self.total_amount,
    #                                         'order_id': sale_obj.id
    #                                         })
    #     for each in self:
    #         for obj in each.order_lines:
    #             self.env['washing.washing'].create(
    #                 {'name': obj.product_id.name + '-Washing',
    #                  'user_id': obj.washing_type.assigned_person.id,
    #                  'description': obj.description,
    #                  'laundry_obj': obj.id,
    #                  'state': 'draft',
    #                  'washing_date': datetime.now().strftime(
    #                      '%Y-%m-%d %H:%M:%S')})
    
    # def create_invoice(self):
    #     if self.sale_obj.state in ['draft', 'sent']:
    #         self.sale_obj.action_confirm()
    #     self.invoice_status = self.sale_obj.invoice_status
    #     return {
    #         'name': 'Create Invoice',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'sale.advance.payment.inv',
    #         'type': 'ir.actions.act_window',
    #         'context': {'laundry_sale_obj': self.sale_obj.id},
    #         'target': 'new'
    #     }

    def _default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.id

    def _default_tax(self):
        tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale')], limit=1)
        return tax.id

    def _default_narration(self):
        terms = self.env['ir.config_parameter'].sudo().get_param('invoice_terms') or False
        return terms

    def create_invoice(self):
        if self.state == 'draft':
            raise UserError(_("Please confirm Order First before proceeding to Invoice"))
        # if not self.bl_ref:
        #     raise UserError(_("Please add Bill of Lading Reference."))
        for rec in self:
            product_lines = []
            for ln in rec.order_lines:
                product_lines.append((0,0,{
                    'product_id': ln.product_id.id,
                    'name': ln.description, #ln.product_id.name,
                    'quantity': ln.quantity/1,
                    'price_unit': ln.price_unit,
                    'tax_ids':ln.tax_id,
                }))

            invoice = {
                    'ref': rec.name,
                    'partner_id' : rec.partner_id.id,
                    'move_type': 'out_invoice',
                    'currency_id': rec.currency_id.id,
                    'laundry_id' : rec.id,
                    'payment_reference' : rec.name,
                    'journal_id' : self._default_journal(),
                    'narration': rec.note,
                    # 'default_customs_bill':True,
                    'invoice_line_ids':product_lines,
                }
            inv_id = self.env['account.move'].create(invoice)
            rec.write({
                'invoice_id':inv_id.id
            })
            # page_directory_search = request.env['ir.model.data'].sudo()._xmlid_lookup('module.xml_id')
            # wiz_form_id = self.env['ir.model.data']._xmlid_lookup('account', 'view_move_form')[1]
            return {
                'view_type': 'form',
                # 'view_id': wiz_form_id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': inv_id.id,
                # 'context': context,
            }
    
    def return_dress(self):
        self.state = 'return'
    
    def cancel_order(self):
        self.state = 'cancel'
    
    def _invoice_count(self):
        print('hello')
        # wrk_ordr_ids = self.env['account.move'].search([('invoice_origin', '=', self.sale_obj.name)])
        self.invoice_count = 0
        if self.invoice_id:
            wrk_ordr_ids = self.env['account.move'].search([('laundry_id.id', '=', self.id)])
            self.invoice_count = len(wrk_ordr_ids)
        print('Hi')
    
    def _work_count(self):
        if self.id:
            wrk_ordr_ids = self.env['washing.washing'].search([('laundry_obj.laundry_obj.id', '=', self.id)])
            self.work_count = len(wrk_ordr_ids)
        else:
            self.work_count = False

    def action_view_laundry_works(self):
        
        work_obj = self.env['washing.washing'].search(
            [('laundry_obj.laundry_obj.id', '=', self.id)])
        print(work_obj)
        work_ids = []
        for each in work_obj:
            work_ids.append(each.id)
        view_id = self.env.ref('laundry.washing_form_view').id
        if work_ids:
            if len(work_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'washing.washing',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    'res_id': work_ids and work_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', work_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'washing.washing',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    'res_id': work_ids
                }
            
            return value
    
    def action_view_invoice(self):
        
        inv_obj = self.env['account.move'].search(
            [('invoice_origin', '=', self.sale_obj.name)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.view_move_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids
                }
            
            return value

    @api.model
    def _get_employee(self):
        """Return default physician value"""
        hr_obj = self.env['hr.employee']
        domain = [('user_id', '=', self.env.uid)]
        user_ids = hr_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False
    
    name = fields.Char(string="Label", copy=False, default='/')
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', invisible=1, related='sale_obj.invoice_status',
        store=True)
    sale_obj = fields.Many2one('sale.order', invisible=1)
    invoice_id = fields.Many2one('account.move', 'Invoice')
    invoice_count = fields.Integer(compute='_invoice_count',
                                   string='# Invoice')
    work_count = fields.Integer(compute='_work_count', string='# Works')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'order': [('readonly', False)]},
                                 required=True,
                                 change_default=True, index=True,
                                 track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         readonly=True,
                                         states={
                                             'draft': [('readonly', False)],
                                             'order': [('readonly', False)]},
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Delivery Address',
                                          readonly=True,
                                          states={
                                              'draft': [('readonly', False)],
                                              'order': [('readonly', False)]},
                                          help="Delivery address for current sales order.")
    order_date = fields.Datetime(string="Date",
                                 default=datetime.now().strftime(
                                     '%Y-%m-%d %H:%M:%S'))
    laundry_person = fields.Many2one('res.users', string='Laundry Person',
                                     required=1)
    order_lines = fields.One2many('laundry.order.line', 'laundry_obj',
                                  required=1, ondelete='cascade')
    total_amount = fields.Float(compute='get_total', string='Total', store=1)
    currency_id = fields.Many2one("res.currency", string="Currency")
    note = fields.Text(string='Terms and conditions')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'Laundry Order'),
        ('process', 'Processing'),
        ('done', 'Done'),
        ('return', 'Returned'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        track_visibility='onchange', default='draft')
    employee_id = fields.Many2one('hr.employee', 'Generated by', \
        domain="[('user_id','=',self.user_id)]", default=_get_employee, tracking=True)
    outlet = fields.Many2one('laundry.outlet', 'Outlet/Shop')
    pricelist = fields.Many2one('product.pricelist', 'Pricelist')
    company_id = fields.Many2one('res.company', default=1)

    @api.onchange('employee_id')
    def _change_outlet(self):
        for rec in self:
            rec.outlet = rec.employee_id.outlet.id
            rec.laundry_person = rec.employee_id.user_id.id

    @api.onchange('outlet')
    def _change_pricelist(self):
        for rec in self:
            rec.pricelist = rec.outlet.pricelist.id

    @api.onchange('partner_id')
    def _change_invoice_shipping_address(self):
        for rec in self:
            rec.partner_invoice_id = rec.partner_id.id
            rec.partner_shipping_id = rec.partner_id.id

    def confirm_order(self):
        """
        This method will change the state to Approve state.
        ---------------------------------------------------
        """
        for rec in self:
            seq_name = ""
            # for rec in self:
            if rec.outlet:                    
                seq_name = rec.outlet.sequence_id.next_by_id()
                rec.write({
                    'name':seq_name,
                    # 'sequence_id': seq.id,
                })
            else:
                raise UserError(_(
                    'The Outlet is not Set! \n ' 
                    'Please add the Outlet.'))
            if not rec.order_lines:
                raise UserError(_(
                    'Please add atleast 1 order item!'
                    ))

            # for each in self:
            for obj in rec.order_lines:
                self.env['washing.washing'].create(
                    {'name': obj.product_id.name,
                    # 'user_id': obj.washing_type.assigned_person.id,
                    'description': obj.description,
                    'laundry_obj': obj.id,
                    'state': 'draft',
                    'washing_date': datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S')})
              
            rec.state = 'order'

    @api.constrains("pricelist", "currency_id")
    def _check_currency(self):
        for sel in self:
            if sel.pricelist.currency_id != sel.currency_id:
                raise UserError(
                    _("Pricelist and Order need to use the same currency.")
                )
                
    @api.onchange("pricelist")
    def _set_pricelist_currency(self):
        self.currency_id = self.pricelist.currency_id


class LaundryManagementLine(models.Model):
    _name = 'laundry.order.line'
    
    @api.depends('product_id', 'extra_work', 'quantity',"express")
    def get_amount(self):
        for obj in self:
            obj._onchange_product_id_pricelist()
            total = obj.price_unit * obj.quantity
            for each in obj.extra_work:
                total += each.amount * obj.quantity
            obj.amount = total
            
    def _default_tax(self):
        tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale')], limit=1)
        return tax.id
    
    product_id = fields.Many2one('product.product', string='Service', required=1)
    quantity = fields.Integer(string='No of items', required=1, default=1)
    description = fields.Text(string='Description')
    washing_type = fields.Many2one('washing.type', string='Washing Type',)
    extra_work = fields.Many2many('washing.work', string='Extra Work')
    express = fields.Boolean("Express ")
    price_unit = fields.Float(string='Unit Price',)
    amount = fields.Float(compute='get_amount', string='Total')
    laundry_obj = fields.Many2one('laundry.order', invisible=1)
    tax_id = fields.Many2one("account.tax", default=_default_tax)
    company_id = fields.Many2one('res.company', default=1)
    discount = fields.Integer('Discount(%)')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wash', 'In Progress'),
        ('extra_work', 'Make Over'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')

    # @api.onchange('product_id')
    # def _product_change_product(self):
    #     for rec in self:
    #         rec.price_unit = rec.product_id.lst_price

    

    @api.onchange("product_id", "quantity","express")
    def _onchange_product_id_pricelist(self):
        for sel in self:
            sel.price_unit = sel.product_id.lst_price * 2 if self.express else sel.product_id.lst_price
            if not sel.laundry_obj.pricelist:
                return
            sel.with_context(check_move_validity=False).update(
                {"price_unit": sel._get_price_with_pricelist()}
            )
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        PricelistItem = self.env["product.pricelist.item"]
        field_name = "lst_price"
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            while (
                pricelist_item.base == "pricelist"
                and pricelist_item.base_pricelist_id
                and pricelist_item.base_pricelist_id.discount_policy
                == "without_discount"
            ):
                price, rule_id = pricelist_item.base_pricelist_id.with_context(
                    uom=uom.id
                ).get_product_price_rule(product, qty, self.laundry_obj.partner_id)
                pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == "standard_price":
                field_name = "standard_price"
                product_currency = product.cost_currency_id
            elif (
                pricelist_item.base == "pricelist" and pricelist_item.base_pricelist_id
            ):
                field_name = "price"
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id
                )
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency,
                    currency_id,
                    self.company_id or self.env.company,
                    self.laundry_obj.invoice_date or fields.Date.today(),
                )

        product_uom = self.env.context.get("uom") or product.uom_id.id
        if uom and uom.id != product_uom:
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    def _calculate_discount(self, base_price, final_price):
        discount = (base_price - final_price) / base_price * 100
        if (discount < 0 and base_price > 0) or (discount > 0 and base_price < 0):
            discount = 0.0
        return discount

    def _get_price_with_pricelist(self):
        price_unit = 0.0
        if self.laundry_obj.pricelist and self.product_id:
            if self.laundry_obj.pricelist.discount_policy == "with_discount":
                product = self.product_id.with_context(
                    lang=self.laundry_obj.partner_id.lang,
                    partner=self.laundry_obj.partner_id.id,
                    quantity=self.quantity,
                    date_order=self.laundry_obj.order_date,
                    pricelist=self.laundry_obj.pricelist.id,
                    product_uom_id=self.product_id.uom_id.id,
                    fiscal_position=(
                        self.laundry_obj.partner_id.property_account_position_id.id
                    ),
                )
                tax_obj = self.env["account.tax"]
                recalculated_price_unit = (
                    product.list_price * self.product_id.uom_id.factor
                ) / (self.product_id.uom_id.factor or 1.0)
                price_unit = tax_obj._fix_tax_included_price_company(
                    recalculated_price_unit,
                    product.taxes_id,
                    self.tax_id,
                    self.company_id,
                )
                self.with_context(check_move_validity=False).discount = 0.0
            else:
                product_context = dict(
                    self.env.context,
                    partner_id=self.laundry_obj.partner_id.id,
                    date=self.laundry_obj.invoice_date or fields.Date.today(),
                    uom=self.product_id.uom_id.id,
                )
                final_price, rule_id = self.laundry_obj.pricelist.with_context(
                    product_context
                ).get_product_price_rule(
                    self.product_id, self.quantity or 1.0, self.laundry_obj.partner_id
                )
                base_price, currency = self.with_context(
                    product_context
                )._get_real_price_currency(
                    self.product_id,
                    rule_id,
                    self.quantity,
                    self.product_id.uom_id,
                    self.laundry_obj.pricelist.id,
                )
                if currency != self.laundry_obj.pricelist.currency_id:
                    base_price = currency._convert(
                        base_price,
                        self.laundry_obj.pricelist.currency_id,
                        self.laundry_obj.company_id or self.env.company,
                        self.laundry_obj.order_date or fields.Date.today(),
                    )
                price_unit = max(base_price, final_price)
                self.with_context(
                    check_move_validity=False
                ).discount = self._calculate_discount(base_price, final_price)
        return price_unit


class WashingType(models.Model):
    _name = 'washing.type'
    
    name = fields.Char(string='Name', required=1)
    assigned_person = fields.Many2one('res.users', string='Assigned Person',
                                      required=1)
    amount = fields.Float(string='Service Charge', required=1)


class ExtraWork(models.Model):
    _name = 'washing.work'
    
    name = fields.Char(string='Name', required=1)
    assigned_person = fields.Many2one('res.users', string='Assigned Person',
                                      required=1)
    amount = fields.Float(string='Service Charge', required=1)


class Washing(models.Model):
    _name = 'washing.washing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    def start_wash(self):
        if not self.laundry_works:
            self.laundry_obj.state = 'wash'
            self.laundry_obj.laundry_obj.state = 'process'
        # for each in self:
        #     for obj in each.product_line:
        #         self.env['sale.order.line'].create(
        #             {'product_id': obj.product_id.id,
        #              'name': obj.name,
        #              'price_unit': obj.price_unit,
        #              'order_id': each.laundry_obj.laundry_obj.sale_obj.id,
        #              'product_uom_qty': obj.quantity,
        #              'product_uom': obj.uom_id.id,
        #              })
        self.state = 'process'
    
    def set_to_done(self):
        self.state = 'done'
        f = 0
        if not self.laundry_works:
            if self.laundry_obj.extra_work:
                for each in self.laundry_obj.extra_work:
                    self.create({'name': each.name,
                                 'user_id': each.assigned_person.id,
                                 'description': self.laundry_obj.description,
                                 'laundry_obj': self.laundry_obj.id,
                                 'state': 'draft',
                                 'laundry_works': True,
                                 'washing_date': datetime.now().strftime(
                                     '%Y-%m-%d %H:%M:%S')})
                self.laundry_obj.state = 'extra_work'
        laundry_obj = self.search([('laundry_obj.laundry_obj', '=',
                                    self.laundry_obj.laundry_obj.id)])
        for each in laundry_obj:
            if each.state != 'done' or each.state == 'cancel':
                f = 1
                break
        if f == 0:
            self.laundry_obj.laundry_obj.state = 'done'
        laundry_obj1 = self.search([('laundry_obj', '=', self.laundry_obj.id)])
        f1 = 0
        for each in laundry_obj1:
            if each.state != 'done' or each.state == 'cancel':
                f1 = 1
                break
        if f1 == 0:
            self.laundry_obj.state = 'done'
    
    @api.depends('product_line')
    def get_total(self):
        total = 0
        for obj in self:
            for each in obj.product_line:
                total += each.subtotal
            obj.total_amount = total
    
    name = fields.Char(string='Work')
    laundry_works = fields.Boolean(default=False, invisible=1)
    user_id = fields.Many2one('res.users', string='Assigned Person')
    washing_date = fields.Datetime(string='Date')
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    laundry_obj = fields.Many2one('laundry.order.line', invisible=1)
    product_line = fields.One2many('wash.order.line', 'wash_obj',
                                   string='Products', ondelete='cascade')
    total_amount = fields.Float(compute='get_total', string='Grand Total')


class SaleOrderInherit(models.Model):
    _name = 'wash.order.line'
    
    @api.depends('price_unit', 'quantity')
    def compute_amount(self):
        total = 0
        for obj in self:
            total += obj.price_unit * obj.quantity
        obj.subtotal = total
    
    wash_obj = fields.Many2one('washing.washing', string='Order Reference',
                               ondelete='cascade')
    name = fields.Text(string='Description', required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True)
    quantity = fields.Integer(string='Quantity')
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float('Unit Price', default=0.0,
                              related='product_id.list_price')
    subtotal = fields.Float(compute='compute_amount', string='Subtotal',
                            readonly=True, store=True)


class LaundryManagementInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    
    def create_invoices(self):
        context = self._context
        if context.get('laundry_sale_obj'):
            sale_orders = self.env['sale.order'].browse(
                context.get('laundry_sale_obj'))
        else:
            sale_orders = self.env['sale.order'].browse(
                self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            sale_orders._create_invoices()
        elif self.advance_payment_method == 'all':
            sale_orders._create_invoices()(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default(
                    'sale.config.settings', 'deposit_product_id_setting',
                    self.product_id.id)
            
            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered'
                        ' quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another "
                        "product or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda
                        r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
    
    def _create_invoice(self, order, so_line, amount):
        if (
                self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(
                _('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.fixed_amount
            name = _('Down Payment')
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'invoice_payment_ref': order.client_order_ref,
            'invoice_payment_term_id': order.payment_term_id.id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            })],
        }
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice,
                                               'origin': order},
                                       subtype_id=self.env.ref(
                                           'mail.mt_note').id)
        return invoice
