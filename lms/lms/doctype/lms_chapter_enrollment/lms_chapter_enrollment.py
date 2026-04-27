import frappe
from frappe.model.document import Document


class LMSChapterEnrollment(Document):
	def before_insert(self):
		self.granted_by = frappe.session.user
		self.granted_on = frappe.utils.today()

	def validate(self):
		existing = frappe.db.get_value(
			"LMS Chapter Enrollment",
			{"member": self.member, "course": self.course, "name": ("!=", self.name)},
			"name",
		)
		if existing:
			frappe.throw(
				frappe._(
					"An enrollment record already exists for {0} in this course. "
					"Please edit the existing record to add or remove chapters."
				).format(self.member)
			)
