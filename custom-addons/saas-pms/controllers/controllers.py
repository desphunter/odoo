# -*- coding: utf-8 -*-
# from odoo import http


# class Saas-pms(http.Controller):
#     @http.route('/saas-pms/saas-pms/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/saas-pms/saas-pms/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('saas-pms.listing', {
#             'root': '/saas-pms/saas-pms',
#             'objects': http.request.env['saas-pms.saas-pms'].search([]),
#         })

#     @http.route('/saas-pms/saas-pms/objects/<model("saas-pms.saas-pms"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('saas-pms.object', {
#             'object': obj
#         })
