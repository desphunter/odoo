# -*- coding: utf-8 -*-
# from odoo import http


# class Saas-pms(http.Controller):
#     @http.route('/idem/idem/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/idem/idem/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('idem.listing', {
#             'root': '/idem/idem',
#             'objects': http.request.env['idem.idem'].search([]),
#         })

#     @http.route('/idem/idem/objects/<model("idem.idem"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('idem.object', {
#             'object': obj
#         })
