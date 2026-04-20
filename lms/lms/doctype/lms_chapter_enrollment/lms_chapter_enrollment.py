import frappe
from frappe.model.document import Document


class LMSChapterEnrollment(Document):
	def before_insert(self):
		self.granted_by = frappe.session.user
		self.granted_on = frappe.utils.today()

	def validate(self):
		if frappe.db.exists(
			"LMS Chapter Enrollment",
			{"member": self.member, "course": self.course, "chapter": self.chapter, "name": ("!=", self.name)},
		):
			frappe.throw(frappe._("{0} already has access to this chapter.").format(self.member))
