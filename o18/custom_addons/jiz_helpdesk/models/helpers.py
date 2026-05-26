from odoo import _

def validate_documents(self):
    required_doc_types_list = []
    required_doc_types = ""

    doc_types = self.env["jiz.document.type"].sudo().search([('type', '=', 'ataa')]) 
    for type in doc_types:
        doc_types_flag = False
        
        domain = [
            '|',
                ('type', '=', 'folder'),
                '&',
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
        ]

        documents = self.env["documents.document"].sudo().search(domain)

        # Documents
        flag_found = False
        for document in documents:
            if document.doc_type:
                if type.id == document.doc_type.id:
                    flag_found = True

        if not flag_found:
            if type.is_mandatory:
                doc_types_flag = True

        if doc_types_flag:
            required_doc_types += _("Please Upload ") + type.name + _(" Document") + "\n"
            required_doc_types_list.append({
                "label":type.name or '',
                "description":type.description or '',
                "is_mandatory":type.is_mandatory,
            })

    return {
        "types_list":required_doc_types_list,
        "types":required_doc_types,
    }