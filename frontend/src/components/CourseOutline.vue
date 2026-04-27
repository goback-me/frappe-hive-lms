<template>
	<div class="">
		<div
			v-if="title && (outline.data?.length || allowEdit)"
			class="flex items-center justify-between gap-x-2 mb-4 px-2"
			:class="{
				'sticky top-0 z-10 bg-surface-white border-b px-3 py-2.5 sm:px-5':
					allowEdit,
			}"
		>
			<div
				class="font-semibold text-lg leading-5 text-ink-gray-9"
				:class="{ 'font-medium text-p-base': allowEdit }"
			>
				{{ __(title) }}
			</div>
			<Button size="sm" v-if="allowEdit" @click="openChapterModal()">
				<template #prefix>
					<Plus class="size-4 stroke-1.5" />
				</template>
				{{ __('Add') }}
			</Button>
		</div>
		<div
			:class="{
				'border-2 rounded-md py-2 px-2': showOutline && outline.data?.length,
			}"
		>
			<Draggable
				:list="outline.data"
				:disabled="!allowEdit"
				item-key="name"
				group="chapters"
				@end="updateChapterOrder"
			>
				<template #item="{ element: chapter, index }">
					<div class="chapter-item">
						<Disclosure
							v-slot="{ open }"
							:key="chapter.name"
							:defaultOpen="openChapterDetail(chapter.idx)"
						>
							<!-- Wrapper row: DisclosureButton as div avoids nested <button> HTML issue -->
							<!-- Clicking anywhere on a locked row opens the lock modal -->
							<div
								class="flex items-center w-full p-2 group"
								:class="{ 'cursor-pointer': chapter.is_locked }"
								@click="chapter.is_locked ? showLockedModal(chapter) : null"
							>
								<DisclosureButton
									as="div"
									class="flex items-center flex-1 min-w-0"
									:class="chapter.is_locked ? 'pointer-events-none' : 'cursor-pointer'"
								>
									<ChevronRight
										:class="{
											'rotate-90': open,
											'rtl:rotate-180': !open,
											hidden: chapter.is_scorm_package || chapter.is_locked,
											open: index == 1,
										}"
										class="h-4 w-4 text-ink-gray-9 stroke-1 transform duration-200 shrink-0"
									/>
									<LockKeyhole
										v-if="chapter.is_locked"
										class="h-4 w-4 text-ink-gray-5 stroke-1.5 shrink-0"
									/>
									<div
										class="text-base text-start font-medium leading-5 ms-2 truncate"
										:class="chapter.is_locked ? 'text-ink-gray-5' : 'text-ink-gray-9'"
										@click="redirectToChapter(chapter)"
									>
										{{ chapter.title }}
									</div>
								</DisclosureButton>
								<div class="flex ms-auto gap-x-4 items-center shrink-0">
									<Tooltip :text="__('Edit Chapter')" placement="bottom">
										<FilePenLine
											v-if="allowEdit"
											@click.stop="openChapterModal(chapter)"
											class="h-4 w-4 text-ink-gray-9 invisible group-hover:visible"
										/>
									</Tooltip>
									<Tooltip :text="__('Delete Chapter')" placement="bottom">
										<Trash2
											v-if="allowEdit"
											@click.stop="trashChapter(chapter.name)"
											class="h-4 w-4 text-ink-red-3 invisible group-hover:visible"
										/>
									</Tooltip>
								</div>
								<Check
									v-if="chapter.is_scorm_package && isScormChapterComplete(chapter)"
									class="h-4 w-4 text-green-700 shrink-0"
								/>
							</div>
							<DisclosurePanel v-if="!chapter.is_scorm_package && !chapter.is_locked">
								<Draggable
									v-if="!chapter.is_scorm_package"
									:list="chapter.lessons"
									:disabled="!allowEdit"
									item-key="name"
									group="items"
									@end="updateOutline"
									:data-chapter="chapter.name"
								>
									<template #item="{ element: lesson }">
										<div
											class="outline-lesson ps-8 py-2 pe-4 text-ink-gray-9"
											:class="
												isActiveLesson(lesson.number) ? 'bg-surface-gray-3' : ''
											"
										>
											<router-link
												:to="{
													name: allowEdit ? 'LessonForm' : 'Lesson',
													params: {
														courseName: courseName,
														chapterNumber: lesson.number.split('-')[0],
														lessonNumber: lesson.number.split('-')[1],
													},
												}"
											>
												<div class="flex items-center text-sm leading-5 group">
													<MonitorPlay
														v-if="lesson.icon === 'icon-youtube'"
														class="h-4 w-4 stroke-1 me-2"
													/>
													<HelpCircle
														v-else-if="lesson.icon === 'icon-quiz'"
														class="h-4 w-4 stroke-1 me-2"
													/>
													<NotebookPen
														v-else-if="lesson.icon === 'icon-assignment'"
														class="h-4 w-4 stroke-1 me-2"
													/>
													<SquareCode
														v-else-if="lesson.icon === 'icon-code'"
														class="h-4 w-4 stroke-1 me-2"
													/>
													<FileText
														v-else-if="lesson.icon === 'icon-list'"
														class="h-4 w-4 text-ink-gray-9 stroke-1 me-2"
													/>
													{{ lesson.title }}
													<Trash2
														v-if="allowEdit"
														@click.prevent="
															trashLesson(lesson.name, chapter.name)
														"
														class="h-4 w-4 text-ink-red-3 ms-auto invisible group-hover:visible"
													/>
													<Check
														v-if="lesson.is_complete"
														class="h-4 w-4 text-green-700 ms-2"
													/>
												</div>
											</router-link>
										</div>
									</template>
								</Draggable>
								<div v-if="allowEdit" class="flex mt-2 mb-4 ps-8">
									<router-link
										v-if="!chapter.is_scorm_package"
										:to="{
											name: 'LessonForm',
											params: {
												courseName: courseName,
												chapterNumber: chapter.idx,
												lessonNumber: chapter.lessons.length + 1,
											},
										}"
									>
										<Button>
											{{ __('Add Lesson') }}
										</Button>
									</router-link>
								</div>
							</DisclosurePanel>
						</Disclosure>
					</div>
				</template>
			</Draggable>
		</div>
	</div>
	<ChapterModal
		v-if="user.data"
		v-model="showChapterModal"
		v-model:outline="outline"
		:course="courseName"
		:chapterDetail="getCurrentChapter()"
	/>

	<!-- Locked Chapter Modal -->
	<Teleport to="body">
		<Transition name="locked-modal">
			<div
				v-if="lockedModalVisible"
				class="fixed inset-0 z-50 flex items-center justify-center p-4"
				@click.self="lockedModalVisible = false"
			>
				<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="lockedModalVisible = false" />
				<div class="locked-modal-card relative bg-surface-white rounded-2xl shadow-2xl p-10 max-w-sm w-full flex flex-col items-center text-center gap-4">
					<button
						class="absolute top-4 right-4 text-ink-gray-4 hover:text-ink-gray-7 transition-colors"
						@click="lockedModalVisible = false"
					>
						<X class="h-5 w-5" />
					</button>
					<div class="lock-icon-wrapper flex items-center justify-center w-20 h-20 rounded-full bg-surface-gray-2">
						<LockKeyhole class="h-9 w-9 text-ink-gray-5 stroke-1.5" />
					</div>
					<div>
						<p class="text-xl font-semibold text-ink-gray-9 mb-1">
							{{ __('This section is locked') }}
						</p>
						<p class="text-sm text-ink-gray-5 leading-relaxed">
							{{ __('Get approval on the previous sections to unlock') }}
						</p>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
<script setup>
import { Button, createResource, Tooltip, toast } from 'frappe-ui'
import { getCurrentInstance, inject, ref, watch } from 'vue'
import Draggable from 'vuedraggable'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue'
import {
	Check,
	ChevronRight,
	FileText,
	FilePenLine,
	HelpCircle,
	LockKeyhole,
	MonitorPlay,
	NotebookPen,
	Plus,
	SquareCode,
	Trash2,
	X,
} from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import ChapterModal from '@/components/Modals/ChapterModal.vue'

const route = useRoute()
const router = useRouter()
const user = inject('$user')
const showChapterModal = ref(false)
const currentChapter = ref(null)
const lockedModalVisible = ref(false)
const activeLockedChapter = ref(null)
const app = getCurrentInstance()
const { $dialog } = app.appContext.config.globalProperties

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	showOutline: {
		type: Boolean,
		default: false,
	},
	title: {
		type: String,
		default: '',
	},
	allowEdit: {
		type: Boolean,
		default: false,
	},
	getProgress: {
		type: Boolean,
		default: false,
	},
	lessonProgress: {
		type: Number,
		default: 0,
	},
})

const outline = createResource({
	url: 'lms.lms.utils.get_course_outline',
	cache: ['course_outline', props.courseName, user.data?.name || 'guest'],
	makeParams() {
		return {
			course: props.courseName,
			progress: props.getProgress,
		}
	},
	auto: true,
})

watch(
	() => props.courseName,
	() => {
		outline.reload()
	}
)

watch(
	() => props.lessonProgress,
	() => {
		outline.reload()
	}
)

const deleteLesson = createResource({
	url: 'lms.lms.api.delete_lesson',
	makeParams(values) {
		return {
			lesson: values.lesson,
			chapter: values.chapter,
		}
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Lesson deleted successfully'))
	},
})

const updateLessonIndex = createResource({
	url: 'lms.lms.api.update_lesson_index',
	makeParams(values) {
		return {
			lesson: values.lesson,
			sourceChapter: values.sourceChapter,
			targetChapter: values.targetChapter,
			idx: values.idx,
		}
	},
	onSuccess() {
		toast.success(__('Lesson moved successfully'))
	},
})

const updateChapterIndex = createResource({
	url: 'lms.lms.api.update_chapter_index',
	makeParams(values) {
		return {
			chapter: values.chapter,
			course: values.course,
			idx: values.idx,
		}
	},
	onSuccess() {
		toast.success(__('Chapter moved successfully'))
	},
})

const trashLesson = (lessonName, chapterName) => {
	$dialog({
		title: __('Delete this lesson?'),
		message: __(
			'Deleting this lesson will permanently remove it from the course. This action cannot be undone. Are you sure you want to continue?'
		),
		actions: [
			{
				label: __('Delete'),
				theme: 'red',
				variant: 'solid',
				onClick(close) {
					deleteLesson.submit({
						lesson: lessonName,
						chapter: chapterName,
					})
					close()
				},
			},
		],
	})
}

const openChapterDetail = (index) => {
	return index == route.params.chapterNumber || index == 1
}

const openChapterModal = (chapter = null) => {
	currentChapter.value = chapter
	showChapterModal.value = true
}

const getCurrentChapter = () => {
	return currentChapter.value
}

const updateOutline = (e) => {
	updateLessonIndex.submit({
		lesson: e.item.__draggable_context.element.name,
		sourceChapter: e.from.dataset.chapter,
		targetChapter: e.to.dataset.chapter,
		idx: e.newIndex,
	})
}

const updateChapterOrder = (e) => {
	updateChapterIndex.submit({
		chapter: e.item.__draggable_context.element.name,
		course: props.courseName,
		idx: e.newIndex,
	})
}

const deleteChapter = createResource({
	url: 'lms.lms.api.delete_chapter',
	makeParams(values) {
		return {
			chapter: values.chapter,
		}
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Chapter deleted successfully'))
	},
})

const trashChapter = (chapterName) => {
	$dialog({
		title: __('Delete this chapter?'),
		message: __(
			'Deleting this chapter will also delete all its lessons and permanently remove it from the course. This action cannot be undone. Are you sure you want to continue?'
		),
		actions: [
			{
				label: __('Delete'),
				theme: 'red',
				variant: 'solid',
				onClick(close) {
					deleteChapter.submit({ chapter: chapterName })
					close()
				},
			},
		],
	})
}

const showLockedModal = (chapter) => {
	activeLockedChapter.value = chapter
	lockedModalVisible.value = true
}

const redirectToChapter = (chapter) => {
	if (!chapter.is_scorm_package) return
	event.preventDefault()
	if (props.allowEdit) return
	if (!user.data) {
		toast.success(__('Please enroll for this course to view this lesson'))
		return
	}

	router.push({
		name: 'SCORMChapter',
		params: {
			courseName: props.courseName,
			chapterName: chapter.name,
		},
	})
}

const isScormChapterComplete = (chapter) => {
	return chapter.lessons?.length && chapter.lessons.every((l) => l.is_complete)
}

const isActiveLesson = (lessonNumber) => {
	return (
		route.params.chapterNumber == lessonNumber.split('-')[0] &&
		route.params.lessonNumber == lessonNumber.split('-')[1]
	)
}
</script>

<style scoped>
/* Backdrop + card enter/leave transitions */
.locked-modal-enter-active,
.locked-modal-leave-active {
	transition: opacity 0.25s ease;
}
.locked-modal-enter-active .locked-modal-card,
.locked-modal-leave-active .locked-modal-card {
	transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.locked-modal-enter-from,
.locked-modal-leave-to {
	opacity: 0;
}
.locked-modal-enter-from .locked-modal-card {
	opacity: 0;
	transform: scale(0.85) translateY(12px);
}
.locked-modal-leave-to .locked-modal-card {
	opacity: 0;
	transform: scale(0.85) translateY(12px);
}

/* Lock icon bounce-in animation */
.lock-icon-wrapper {
	animation: lock-bounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.15s both;
}
@keyframes lock-bounce {
	from {
		opacity: 0;
		transform: scale(0.5);
	}
	to {
		opacity: 1;
		transform: scale(1);
	}
}
</style>
