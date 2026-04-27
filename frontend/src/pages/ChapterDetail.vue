<template>
	<div v-if="chapter">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
			<div class="flex items-center gap-x-2">
				<Button v-if="chapter.prev" @click="goTo(chapter.prev)">
					<template #prefix>
						<ChevronLeft class="w-4 h-4 stroke-1" />
					</template>
					{{ __('Previous') }}
				</Button>
				<Button v-if="chapter.next" @click="goTo(chapter.next)">
					{{ __('Next') }}
					<template #suffix>
						<ChevronRight class="w-4 h-4 stroke-1" />
					</template>
				</Button>
			</div>
		</header>

		<div class="grid md:grid-cols-[70%,30%] h-[94vh]">
			<!-- Main content area -->
			<div class="border-e overflow-y-auto">
				<div class="pt-5 pb-10 px-5">
					<div class="text-3xl font-semibold text-ink-gray-9 mb-6">
						{{ chapter.title }}
					</div>
					<div
						v-if="chapter.description"
						class="ProseMirror prose prose-sm max-w-none !whitespace-normal"
						v-html="chapter.description"
					/>
					<div v-else class="text-ink-gray-5 text-sm">
						{{ __('No content added to this chapter yet.') }}
					</div>
				</div>
			</div>

			<!-- Right sidebar: course outline -->
			<CourseOutline
				:courseName="courseName"
				:key="chapterNumber"
				:lessonProgress="0"
				:getProgress="true"
				showOutline
			/>
		</div>
	</div>
	<div v-else class="flex items-center justify-center h-40">
		<span class="text-ink-gray-5">{{ __('Loading...') }}</span>
	</div>
</template>

<script setup>
import { Breadcrumbs, Button, createResource, usePageMeta } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import CourseOutline from '@/components/CourseOutline.vue'
import { sessionStore } from '@/stores/session'

const props = defineProps({
	courseName: { type: String, required: true },
	chapterNumber: { type: String, required: true },
})

const router = useRouter()
const { brand } = sessionStore()
const chapter = ref(null)

const outline = createResource({
	url: 'lms.lms.utils.get_course_outline',
	makeParams() {
		return { course: props.courseName, progress: false }
	},
	auto: true,
	onSuccess(data) {
		findChapter(data)
	},
})

const findChapter = (data) => {
	if (!data) return
	const flat = []
	data.forEach((ch) => {
		flat.push(ch)
		if (ch.sub_chapters?.length) {
			ch.sub_chapters.forEach((sub) => flat.push(sub))
		}
	})
	const idx = parseInt(props.chapterNumber)
	const found = flat.find((c) => c.idx === idx)
	if (!found) return

	// build prev/next from flat list
	const i = flat.indexOf(found)
	chapter.value = {
		...found,
		prev: i > 0 ? flat[i - 1] : null,
		next: i < flat.length - 1 ? flat[i + 1] : null,
	}
}

watch(() => props.chapterNumber, () => {
	if (outline.data) findChapter(outline.data)
})

const goTo = (target) => {
	if (target.lessons?.length) {
		const first = target.lessons[0]
		const [cn, ln] = first.number.split('-')
		router.push({ name: 'Lesson', params: { courseName: props.courseName, chapterNumber: cn, lessonNumber: ln } })
	} else {
		router.push({ name: 'ChapterDetail', params: { courseName: props.courseName, chapterNumber: target.idx } })
	}
}

const breadcrumbs = computed(() => [
	{ label: __('Courses'), route: { name: 'Courses' } },
	{ label: props.courseName, route: { name: 'CourseDetail', params: { courseName: props.courseName } } },
	{ label: chapter.value?.title || '', route: {} },
])

usePageMeta(() => ({
	title: chapter.value?.title || __('Chapter'),
	icon: brand.favicon,
}))
</script>
