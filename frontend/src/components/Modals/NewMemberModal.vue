<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Add New Member'),
			size: 'lg',
			actions: [
				{
					label: __('Add'),
					variant: 'solid',
					loading: submitting,
					onClick: ({ close }: any) => addMember(close),
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<FormControl
					v-model="member.email"
					:label="__('Email')"
					placeholder="jane@doe.com"
					type="email"
					:required="true"
					@keyup.enter="addMember()"
				/>
				<div class="flex items-center gap-3">
					<FormControl
						v-model="member.first_name"
						:label="__('First Name')"
						placeholder="Jane"
						type="text"
						class="w-full"
					/>
					<FormControl
						v-model="member.last_name"
						:label="__('Last Name')"
						placeholder="Doe"
						type="text"
						class="w-full"
					/>
				</div>
				<div class="flex flex-col gap-2">
					<div class="text-sm text-ink-gray-5">
						{{ __('Roles') }}
					</div>
					<div class="grid md:grid-cols-2 gap-x-6 gap-y-3">
						<Switch
							size="sm"
							:label="__('Student')"
							v-model="roles.lms_student"
						/>
						<Switch
							size="sm"
							:label="__('Course Creator')"
							v-model="roles.course_creator"
						/>
						<Switch
							size="sm"
							:label="__('Evaluator')"
							v-model="roles.batch_evaluator"
						/>
						<Switch
							size="sm"
							:label="__('Moderator')"
							v-model="roles.moderator"
						/>
					</div>
				</div>

				<!-- Course Access -->
				<div class="border-t pt-4 flex flex-col gap-3">
					<div class="text-sm text-ink-gray-5">
						{{ __('Course Access (optional)') }}
					</div>
					<FormControl
						v-model="selectedCourse"
						:label="__('Course')"
						type="select"
						:options="courseOptions"
						@change="onCourseChange"
					/>
					<div v-if="selectedCourse && chapters.length" class="flex flex-col gap-2">
						<div class="text-sm text-ink-gray-5">
							{{ __('Chapters (leave all unchecked for full course access)') }}
						</div>
						<div class="grid md:grid-cols-2 gap-x-6 gap-y-2 max-h-48 overflow-y-auto">
							<label
								v-for="ch in chapters"
								:key="ch.name"
								class="flex items-center gap-2 cursor-pointer text-sm text-ink-gray-9"
							>
								<input
									type="checkbox"
									:value="ch.name"
									v-model="selectedChapters"
									class="rounded"
								/>
								{{ ch.title }}
							</label>
						</div>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { call, Dialog, FormControl, toast, Switch } from 'frappe-ui'
import { reactive, ref, watch, computed } from 'vue'
import { cleanError } from '@/utils'

const show = defineModel<boolean>({ default: false })
const submitting = ref(false)
const selectedCourse = ref('')
const selectedChapters = ref<string[]>([])
const chapters = ref<{ name: string; title: string }[]>([])
const courseList = ref<{ name: string; title: string }[]>([])

const props = defineProps<{
	defaultRoles?: string[]
}>()

const emit = defineEmits<{
	created: [user: any]
}>()

const ROLE_MAP: Record<string, string> = {
	moderator: 'Moderator',
	course_creator: 'Course Creator',
	batch_evaluator: 'Batch Evaluator',
	lms_student: 'LMS Student',
}

const member = reactive({
	email: '',
	first_name: '',
	last_name: '',
})

const roles = reactive({
	moderator: false,
	course_creator: false,
	batch_evaluator: false,
	lms_student: false,
})

const courseOptions = computed(() => [
	{ label: __('None'), value: '' },
	...courseList.value.map((c) => ({ label: c.title, value: c.name })),
])

const loadCourses = async () => {
	try {
		courseList.value = await call('lms.lms.api.get_courses_for_access')
	} catch {
		courseList.value = []
	}
}

const onCourseChange = async () => {
	selectedChapters.value = []
	chapters.value = []
	if (!selectedCourse.value) return
	try {
		chapters.value = await call('lms.lms.api.get_chapters_for_course', {
			course: selectedCourse.value,
		})
	} catch {
		chapters.value = []
	}
}

const resetForm = () => {
	member.email = ''
	member.first_name = ''
	member.last_name = ''
	selectedCourse.value = ''
	selectedChapters.value = []
	chapters.value = []
	applyDefaultRoles()
}

const applyDefaultRoles = () => {
	roles.moderator = props.defaultRoles?.includes('moderator') ?? false
	roles.course_creator = props.defaultRoles?.includes('course_creator') ?? false
	roles.batch_evaluator =
		props.defaultRoles?.includes('batch_evaluator') ?? false
	roles.lms_student = props.defaultRoles?.includes('lms_student') ?? false
}

watch(show, (isOpen) => {
	if (isOpen) {
		resetForm()
		loadCourses()
	}
})

const assignRoles = async (userEmail: string) => {
	const selectedRoles = Object.entries(roles).filter(([_, checked]) => checked)
	for (const [key, _] of selectedRoles) {
		await call('lms.lms.api.save_role', {
			user: userEmail,
			role: ROLE_MAP[key],
			value: 1,
		})
	}
}

const grantCourseAccess = async (userEmail: string) => {
	if (!selectedCourse.value) return

	if (selectedChapters.value.length > 0) {
		await call('lms.lms.api.grant_chapter_access', {
			member: userEmail,
			course: selectedCourse.value,
			chapters: selectedChapters.value,
		})
	} else {
		await call('frappe.client.insert', {
			doc: {
				doctype: 'LMS Enrollment',
				course: selectedCourse.value,
				member: userEmail,
			},
		})
	}
}

const addMember = async (close?: () => void) => {
	if (!member.email?.trim()) {
		toast.error(__('Email is required'))
		return
	}

	submitting.value = true
	try {
		const user = await call('frappe.client.insert', {
			doc: {
				doctype: 'User',
				email: member.email.trim(),
				first_name: member.first_name.trim() || undefined,
				last_name: member.last_name.trim() || undefined,
			},
		})

		await assignRoles(user.name)
		await grantCourseAccess(user.name)

		// Fire webhook server-side (URL never exposed to frontend)
		call('lms.lms.api.notify_user_created', { user_email: user.name }).catch(() => {})

		toast.success(__('Member added successfully'))
		emit('created', user)
		resetForm()
		close?.()
	} catch (err: any) {
		toast.error(cleanError(err.messages?.[0]) || __('Unable to add member'))
	} finally {
		submitting.value = false
	}
}
</script>
