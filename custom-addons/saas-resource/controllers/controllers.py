# -*- coding: utf-8 -*-
# from odoo import http


# class Saas-resource(http.Controller):
#     @http.route('/saas-resource/saas-resource/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/saas-resource/saas-resource/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('saas-resource.listing', {
#             'root': '/saas-resource/saas-resource',
#             'objects': http.request.env['saas-resource.saas-resource'].search([]),
#         })

#     @http.route('/saas-resource/saas-resource/objects/<model("saas-resource.saas-resource"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('saas-resource.object', {
#             'object': obj
#         })
