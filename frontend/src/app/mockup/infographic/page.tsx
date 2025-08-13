'use client';

import React, { useMemo, useEffect, useState, useRef } from 'react';
import {
	Card,
	CardHeader,
	CardContent,
	CardTitle,
	CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
	Workflow,
	MessageSquare,
	ListOrdered,
	Braces,
	ShieldCheck,
	Activity,
	Layers,
	Info,
} from 'lucide-react';

// Fallback minimal Route icon
const RouteIcon: React.FC<React.SVGProps<SVGSVGElement>> = props => (
	<svg viewBox='0 0 24 24' width={20} height={20} {...props}>
		<path
			d='M4 19a3 3 0 1 0 0-6h-.5A2.5 2.5 0 0 1 1 10.5V6a3 3 0 1 1 6 0v4'
			fill='none'
			stroke='currentColor'
			strokeWidth='2'
			strokeLinecap='round'
			strokeLinejoin='round'
		/>
		<circle cx='4' cy='19' r='1.5' fill='currentColor' />
		<circle cx='19' cy='5' r='1.5' fill='currentColor' />
	</svg>
);

function Section({
	id,
	title,
	icon,
	desc,
	children,
	step,
	badge = 'Coordinator',
}: {
	id: string;
	title: string;
	icon?: React.ReactNode;
	desc?: string;
	children?: React.ReactNode;
	step?: number;
	badge?: string;
}) {
	return (
		<section id={id} className='scroll-mt-24'>
			<div className='flex items-center gap-2'>
				{icon}
				<h2 className='text-xl md:text-2xl font-semibold tracking-tight'>
					{step ? (
						<span className='mr-2 text-primary'>Step {step}:</span>
					) : null}
					{title}
				</h2>
				<Badge variant='secondary' className='ml-2'>
					{badge}
				</Badge>
			</div>
			{desc && (
				<p className='text-sm md:text-base text-muted-foreground mt-1'>
					{desc}
				</p>
			)}
			<div className='mt-4 space-y-4'>{children}</div>
		</section>
	);
}

// Box primitive with improved accessible defaults
function Box({
	x,
	y,
	w,
	h,
	label,
	title,
	fill = 'fill-white dark:fill-slate-900',
	stroke = 'stroke-slate-400 dark:stroke-slate-600',
}: {
	x: number;
	y: number;
	w: number;
	h: number;
	label: string;
	title?: string;
	fill?: string;
	stroke?: string;
}) {
	return (
		<g>
			<title>{title ?? label}</title>
			<rect
				x={x}
				y={y}
				width={w}
				height={h}
				rx={12}
				className={`${fill} ${stroke}`}
				strokeWidth='2'
			/>
			<text
				x={x + w / 2}
				y={y + h / 2 + 4}
				textAnchor='middle'
				className='fill-current text-[13px] text-gray-900 dark:text-white'
			>
				{label}
			</text>
		</g>
	);
}

// One-time arrow head defs per SVG to avoid duplicate IDs
function ArrowHeadDefs({ id = 'arrow-std' }: { id?: string }) {
	return (
		<defs>
			<marker
				id={id}
				markerWidth='8'
				markerHeight='8'
				refX='8'
				refY='4'
				orient='auto'
				markerUnits='strokeWidth'
			>
				<path
					d='M 0 0 L 8 4 L 0 8 z'
					className='fill-indigo-600 dark:fill-indigo-300'
				/>
			</marker>
		</defs>
	);
}

function Arrow({
	d,
	tone = 'stroke-indigo-600',
	markerId = 'arrow-std',
}: {
	d: string;
	tone?: string;
	markerId?: string;
}) {
	return (
		<path
			d={d}
			className={`${tone}`}
			strokeWidth={3}
			fill='none'
			markerEnd={`url(#${markerId})`}
		/>
	);
}

// Small utility button to copy code/primitives
function CopyButton({
	text,
	label = 'Copy',
}: {
	text: string;
	label?: string;
}) {
	const [copied, setCopied] = useState(false);
	return (
		<button
			type='button'
			onClick={async () => {
				await navigator.clipboard.writeText(text);
				setCopied(true);
				setTimeout(() => setCopied(false), 1200);
			}}
			className='text-xs px-2 py-1 rounded border bg-background hover:bg-muted transition-colors'
			aria-label='Copy to clipboard'
		>
			{copied ? 'Copied' : label}
		</button>
	);
}

export default function CoordinatorPage() {
	const year = useMemo(() => new Date().getFullYear(), []);
	// Track active section for TOC highlighting
	const [activeId, setActiveId] = useState<string>('intent');
	const sectionIds = useRef<string[]>([
		'intent',
		'routing',
		'plan',
		'prompt',
		'policy',
		'meta',
	]);

	useEffect(() => {
		const observer = new IntersectionObserver(
			entries => {
				entries.forEach(entry => {
					if (entry.isIntersecting) {
						setActiveId(entry.target.id);
					}
				});
			},
			{ rootMargin: '-40% 0px -50% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] },
		);
		sectionIds.current
			.map(id => document.getElementById(id))
			.filter((el): el is Element => Boolean(el))
			.forEach(el => observer.observe(el));
		return () => observer.disconnect();
	}, []);

	return (
		<div
			className='min-h-screen bg-gradient-to-b from-background to-muted/20 text-foreground'
			data-testid='coord-page-root'
		>
			<header className='sticky top-0 z-40 backdrop-blur bg-background/80 border-b'>
				<div className='mx-auto max-w-7xl px-6 py-3 flex items-center justify-between'>
					<div className='flex items-center gap-2'>
						<Layers className='h-6 w-6' />
						<span className='font-semibold'>Selfrag</span>
						<span className='text-muted-foreground'>
							· Coordinator Workflows
						</span>
					</div>
				</div>
			</header>

			<main className='mx-auto max-w-7xl px-6 md:px-8 py-8 space-y-10'>
				{/* Overview blurb to ground the infographic */}
				<p className='text-sm md:text-base text-muted-foreground -mt-2'>
					The Coordinator is the traffic controller: it determines what should
					happen, in what order, and which service does the work.
				</p>

				{/* Quick in-page navigation with active highlighting */}
				<nav
					aria-label='Section navigation'
					className='-mt-2 mb-2 overflow-x-auto'
				>
					<ul className='flex items-center gap-2 text-sm whitespace-nowrap'>
						{sectionIds.current.map(id => {
							const label =
								id === 'intent'
									? 'Intent'
									: id === 'routing'
									? 'Routing'
									: id === 'plan'
									? 'Plan'
									: id === 'prompt'
									? 'Prompt'
									: id === 'policy'
									? 'Policy'
									: 'Meta';
							const isActive = activeId === id;
							return (
								<li key={id}>
									<a
										className={[
											'px-3 py-1 rounded-md border transition-colors',
											isActive
												? 'bg-primary/90 text-primary-foreground border-transparent'
												: 'bg-background hover:bg-muted',
										].join(' ')}
										href={`#${id}`}
										aria-current={isActive ? 'location' : undefined}
									>
										{label}
									</a>
								</li>
							);
						})}
					</ul>
				</nav>

				{/* Legend for color semantics */}
				<Card className='bg-muted/40'>
					<CardHeader className='pb-2'>
						<div className='flex items-center gap-2'>
							<Info className='h-4 w-4' />
							<CardTitle className='text-sm'>Visual Key</CardTitle>
						</div>
						<CardDescription className='text-xs'>
							Consistent high‑contrast palette for readability in light/dark.
						</CardDescription>
					</CardHeader>
					<CardContent className='text-xs grid sm:grid-cols-3 gap-2'>
						<div className='flex items-center gap-2'>
							<span className='inline-block h-3 w-3 rounded bg-indigo-100 dark:bg-indigo-900 ring-1 ring-indigo-600' />{' '}
							Coordinator
						</div>
						<div className='flex items-center gap-2'>
							<span className='inline-block h-3 w-3 rounded bg-emerald-50 dark:bg-emerald-950 ring-1 ring-emerald-600' />{' '}
							RAG / Retrieval
						</div>
						<div className='flex items-center gap-2'>
							<span className='inline-block h-3 w-3 rounded bg-violet-50 dark:bg-violet-950 ring-1 ring-violet-600' />{' '}
							Memory
						</div>
						<div className='flex items-center gap-2'>
							<span className='inline-block h-3 w-3 rounded bg-amber-50 dark:bg-amber-950 ring-1 ring-amber-600' />{' '}
							Agent
						</div>
						<div className='flex items-center gap-2'>
							<span className='inline-block h-3 w-3 rounded bg-slate-100 dark:bg-slate-900 ring-1 ring-slate-600' />{' '}
							LLM / Neutral
						</div>
					</CardContent>
				</Card>

				{/* Intent Detection */}
				<Section
					id='intent'
					title='Intent Detection'
					step={1}
					icon={<MessageSquare className='h-5 w-5' />}
					desc='Classify the request and choose the processing mode.'
				>
					<Card className='bg-muted/40'>
						<CardContent>
							<figure>
								<svg
									viewBox='0 0 860 220'
									className='w-full h-auto'
									role='img'
									aria-label='Intent detection flow diagram'
									aria-describedby='intent-caption'
								>
									<ArrowHeadDefs />
									<Box x={40} y={80} w={140} h={60} label='Request' />
									<Box
										x={230}
										y={60}
										w={180}
										h={100}
										label='Coordinator'
										fill='fill-indigo-100 dark:fill-indigo-900'
										stroke='stroke-indigo-600 dark:stroke-indigo-400'
									/>
									<Box
										x={470}
										y={20}
										w={140}
										h={50}
										label='Heuristics'
										title='Heuristics: lightweight rules to infer intent quickly'
										fill='fill-emerald-50 dark:fill-emerald-950'
										stroke='stroke-emerald-600 dark:stroke-emerald-400'
									/>
									<Box
										x={470}
										y={90}
										w={140}
										h={50}
										label='Rules'
										title='Deterministic routing rules'
										fill='fill-amber-50 dark:fill-amber-950'
										stroke='stroke-amber-600 dark:stroke-amber-400'
									/>
									<Box
										x={470}
										y={160}
										w={140}
										h={50}
										label='Hints/Mode'
										title='Derived mode and hints for downstream services'
										fill='fill-violet-50 dark:fill-violet-950'
										stroke='stroke-violet-600 dark:stroke-violet-400'
									/>
									<Box
										x={650}
										y={40}
										w={160}
										h={60}
										label='RAG'
										fill='fill-emerald-50 dark:fill-emerald-950'
										stroke='stroke-emerald-600 dark:stroke-emerald-500'
									/>
									<Box
										x={650}
										y={100}
										w={160}
										h={60}
										label='Memory'
										fill='fill-violet-50 dark:fill-violet-950'
										stroke='stroke-violet-600 dark:stroke-violet-500'
									/>
									<Box
										x={650}
										y={160}
										w={160}
										h={60}
										label='Agent'
										fill='fill-amber-50 dark:fill-amber-950'
										stroke='stroke-amber-600 dark:stroke-amber-500'
									/>

									<Arrow d='M 180 110 L 230 110' />
									<Arrow d='M 410 85 L 470 45' />
									<Arrow d='M 410 110 L 470 115' />
									<Arrow d='M 410 135 L 470 185' />
									<Arrow d='M 610 70 L 650 70' tone='stroke-emerald-600' />
									<Arrow d='M 610 125 L 650 130' tone='stroke-violet-600' />
									<Arrow d='M 610 180 L 650 190' tone='stroke-amber-600' />
								</svg>
								<figcaption
									id='intent-caption'
									className='mt-2 text-xs text-muted-foreground'
								>
									Decides whether the request is RAG, Memory, or Agent and
									prepares downstream hints.
								</figcaption>
							</figure>
						</CardContent>
					</Card>
				</Section>

				{/* Routing */}
				<Section
					id='routing'
					title='Routing'
					step={2}
					icon={<RouteIcon className='h-5 w-5' />}
					desc='Send the request to the right services in the right order.'
				>
					<Card className='bg-muted/40'>
						<CardContent>
							<figure>
								<svg
									viewBox='0 0 880 220'
									className='w-full h-auto'
									role='img'
									aria-label='Routing flow diagram'
									aria-describedby='routing-caption'
								>
									<ArrowHeadDefs />
									<Box
										x={40}
										y={80}
										w={140}
										h={60}
										label='Coordinator'
										fill='fill-indigo-100 dark:fill-indigo-900'
										stroke='stroke-indigo-600 dark:stroke-indigo-400'
									/>
									<Box
										x={240}
										y={40}
										w={160}
										h={60}
										label='Retriever'
										title='Retrieve candidate chunks from indexes'
										fill='fill-emerald-50 dark:fill-emerald-950'
										stroke='stroke-emerald-600 dark:stroke-emerald-400'
									/>
									<Box
										x={240}
										y={120}
										w={160}
										h={60}
										label='Memory Read'
										title='Load relevant user/session memory'
										fill='fill-violet-50 dark:fill-violet-950'
										stroke='stroke-violet-600 dark:stroke-violet-400'
									/>
									<Box
										x={440}
										y={40}
										w={160}
										h={60}
										label='Context Builder'
										title='Merge, dedupe, and order context'
										fill='fill-teal-50 dark:fill-teal-950'
										stroke='stroke-teal-600 dark:stroke-teal-400'
									/>
									<Box x={640} y={80} w={180} h={60} label='LLM' />

									<Arrow d='M 180 110 L 240 70' />
									<Arrow d='M 180 110 L 240 150' />
									<Arrow d='M 400 70 L 440 70' tone='stroke-teal-600' />
									<Arrow d='M 400 150 L 440 90' tone='stroke-teal-600' />
									<Arrow d='M 600 70 L 640 110' />
								</svg>
								<figcaption
									id='routing-caption'
									className='mt-2 text-xs text-muted-foreground'
								>
									Routes to Retriever and/or Memory, merges into context, then
									forwards to the LLM.
								</figcaption>
							</figure>
						</CardContent>
					</Card>
				</Section>

				{/* Plan Building */}
				<Section
					id='plan'
					title='Plan Building'
					step={3}
					icon={<ListOrdered className='h-5 w-5' />}
					desc='Choose indices, filters, top‑k, reranker, and token budget.'
				>
					<Card className='bg-muted/40'>
						<CardContent className='text-sm md:text-base'>
							<div className='grid md:grid-cols-2 gap-4'>
								<div>
									<ul className='list-disc ml-5 space-y-1'>
										<li>Indices/collections (e.g., project, team)</li>
										<li>Filters (tags, paths, date ranges, namespace)</li>
										<li>Top‑k candidates & reranker on/off</li>
										<li>Chunk window size & overlap</li>
										<li>Token budget for context</li>
									</ul>
								</div>
								<div>
									<svg
										viewBox='0 0 460 160'
										className='w-full h-auto'
										role='img'
										aria-label='Plan building diagram'
									>
										<Box
											x={20}
											y={20}
											w={120}
											h={40}
											label='Plan'
											fill='fill-indigo-100 dark:fill-indigo-900'
											stroke='stroke-indigo-600 dark:stroke-indigo-400'
										/>
										<Box
											x={170}
											y={20}
											w={120}
											h={40}
											label='Indices'
											title='Which indexes/collections to query'
											fill='fill-emerald-50 dark:fill-emerald-950'
											stroke='stroke-emerald-600 dark:stroke-emerald-400'
										/>
										<Box
											x={170}
											y={70}
											w={120}
											h={40}
											label='Filters'
											title='Metadata, paths, tags, time windows'
											fill='fill-amber-50 dark:fill-amber-950'
											stroke='stroke-amber-600 dark:stroke-amber-400'
										/>
										<Box
											x={170}
											y={120}
											w={120}
											h={40}
											label='Top‑k/Rerank'
											title='Candidate count and optional reranker'
											fill='fill-violet-50 dark:fill-violet-950'
											stroke='stroke-violet-600 dark:stroke-violet-400'
										/>
										<Box
											x={320}
											y={70}
											w={120}
											h={40}
											label='Token budget'
											title='Context length constraints'
											fill='fill-teal-50 dark:fill-teal-950'
											stroke='stroke-teal-600 dark:stroke-teal-400'
										/>
										<Arrow d='M 140 40 L 170 40' />
										<Arrow
											d='M 140 40 C 150 60 150 80 170 90'
											tone='stroke-amber-600'
										/>
										<Arrow
											d='M 140 40 C 150 100 150 120 170 140'
											tone='stroke-violet-600'
										/>
										<Arrow d='M 290 90 L 320 90' tone='stroke-teal-600' />
									</svg>
								</div>
							</div>
						</CardContent>
					</Card>
				</Section>

				{/* Prompt Assembly */}
				<Section
					id='prompt'
					title='Prompt Assembly'
					step={4}
					icon={<Braces className='h-5 w-5' />}
					desc='Combine system instructions, retrieved context, memory snippets, and user input.'
				>
					<Card className='bg-muted/40'>
						<CardContent className='text-sm md:text-base'>
							<div className='grid md:grid-cols-2 gap-4'>
								<div>
									<div className='flex items-center justify-between mb-2'>
										<span className='text-xs text-muted-foreground'>
											Structured prompt object
										</span>
										<CopyButton
											text={`{
  system: "You are Selfrag…",
  context: [
    { doc: "A.pdf", chunk_id: "A#12", cite: "…" },
    { doc: "B.md",  chunk_id: "B#07", cite: "…" }
  ],
  memory: { profile: ["pref:de"], session: ["goal:…"] },
  user: "How does ingestion work?"
}`}
										/>
									</div>
									<pre className='whitespace-pre-wrap text-xs md:text-sm leading-relaxed bg-background/50 p-3 rounded-md border'>
										{`{
  system: "You are Selfrag…",
  context: [
    { doc: "A.pdf", chunk_id: "A#12", cite: "…" },
    { doc: "B.md",  chunk_id: "B#07", cite: "…" }
  ],
  memory: { profile: ["pref:de"], session: ["goal:…"] },
  user: "How does ingestion work?"
}`}
									</pre>
								</div>
								<div>
									<figure>
										<svg
											viewBox='0 0 480 180'
											className='w-full h-auto'
											role='img'
											aria-label='Prompt assembly diagram'
											aria-describedby='prompt-caption'
										>
											<ArrowHeadDefs />
											<Box x={20} y={20} w={120} h={40} label='System' />
											<Box
												x={20}
												y={70}
												w={120}
												h={40}
												label='Context'
												fill='fill-emerald-50 dark:fill-emerald-950'
												stroke='stroke-emerald-600 dark:stroke-emerald-400'
											/>
											<Box
												x={20}
												y={120}
												w={120}
												h={40}
												label='Memory'
												fill='fill-violet-50 dark:fill-violet-950'
												stroke='stroke-violet-600 dark:stroke-violet-400'
											/>
											<Box
												x={180}
												y={70}
												w={120}
												h={40}
												label='User'
												fill='fill-sky-50 dark:fill-sky-950'
												stroke='stroke-sky-600 dark:stroke-sky-400'
											/>
											<Box
												x={340}
												y={70}
												w={120}
												h={40}
												label='Prompt'
												fill='fill-indigo-100 dark:fill-indigo-900'
												stroke='stroke-indigo-600 dark:stroke-indigo-400'
											/>
											<Arrow d='M 140 40 C 220 40 300 40 340 90' />
											<Arrow d='M 140 90 L 340 90' tone='stroke-emerald-600' />
											<Arrow
												d='M 140 140 C 220 140 300 140 340 90'
												tone='stroke-violet-600'
											/>
											<Arrow d='M 300 90 L 340 90' tone='stroke-sky-600' />
										</svg>
										<figcaption
											id='prompt-caption'
											className='mt-2 text-xs text-muted-foreground'
										>
											Combines System, Context, Memory, and User inputs into a
											single prompt.
										</figcaption>
									</figure>
								</div>
							</div>
						</CardContent>
					</Card>
				</Section>

				{/* Policy Enforcement */}
				<Section
					id='policy'
					title='Policy Enforcement'
					step={5}
					icon={<ShieldCheck className='h-5 w-5' />}
					desc='Apply permissions, PII guards, and namespace/freshness limits before inference.'
				>
					<Card className='bg-muted/40'>
						<CardContent>
							<figure>
								<svg
									viewBox='0 0 840 220'
									className='w-full h-auto'
									role='img'
									aria-label='Policy enforcement diagram'
									aria-describedby='policy-caption'
								>
									<ArrowHeadDefs />
									<Box
										x={40}
										y={80}
										w={140}
										h={60}
										label='Prompt'
										fill='fill-indigo-100 dark:fill-indigo-900'
										stroke='stroke-indigo-600 dark:stroke-indigo-400'
									/>
									<Box
										x={240}
										y={40}
										w={160}
										h={60}
										label='AuthZ'
										title='Authorization and access controls'
										fill='fill-emerald-50 dark:fill-emerald-950'
										stroke='stroke-emerald-600 dark:stroke-emerald-400'
									/>
									<Box
										x={240}
										y={120}
										w={160}
										h={60}
										label='PII Guard'
										title='PII redaction and policy filters'
										fill='fill-amber-50 dark:fill-amber-950'
										stroke='stroke-amber-600 dark:stroke-amber-400'
									/>
									<Box
										x={440}
										y={80}
										w={160}
										h={60}
										label='Namespace/Scope'
										title='Tenant scoping and freshness windows'
										fill='fill-violet-50 dark:fill-violet-950'
										stroke='stroke-violet-600 dark:stroke-violet-400'
									/>
									<Box x={640} y={80} w={140} h={60} label='LLM' />

									<Arrow d='M 180 110 L 240 70' />
									<Arrow d='M 180 110 L 240 150' tone='stroke-amber-600' />
									<Arrow d='M 400 70 L 440 110' tone='stroke-violet-600' />
									<Arrow d='M 600 110 L 640 110' />
								</svg>
								<figcaption
									id='policy-caption'
									className='mt-2 text-xs text-muted-foreground'
								>
									Applies AuthZ, PII redaction, and scoping before sending to
									the LLM.
								</figcaption>
							</figure>
							<div className='text-xs md:text-sm text-muted-foreground mt-3 grid md:grid-cols-3 gap-2'>
								<div>✅ Row‑level security (Postgres), signed URLs (MinIO)</div>
								<div>🧹 Redaction rules & regex policies for PII</div>
								<div>🗂️ Per‑tenant namespaces & freshness windows</div>
							</div>
						</CardContent>
					</Card>
				</Section>

				{/* Meta / Tracing */}
				<Section
					id='meta'
					title='Meta / Tracing'
					step={6}
					icon={<Activity className='h-5 w-5' />}
					desc='Emit structured events for observability and audits.'
				>
					<Card className='bg-muted/40'>
						<CardContent className='text-sm md:text-base'>
							<div className='grid md:grid-cols-2 gap-4'>
								<div>
									<ul className='list-disc ml-5 space-y-1'>
										<li>Request ID, mode, plan parameters</li>
										<li>Used services (retriever, memory, llm)</li>
										<li>Timings: retrieve_ms, rerank_ms, gen_ms</li>
										<li>Context provenance (chunk IDs, citations)</li>
									</ul>
								</div>
								<div>
									<svg
										viewBox='0 0 460 160'
										className='w-full h-auto'
										role='img'
										aria-label='Meta tracing diagram'
									>
										<Box
											x={20}
											y={20}
											w={120}
											h={40}
											label='Coordinator'
											fill='fill-indigo-100 dark:fill-indigo-900'
											stroke='stroke-indigo-600 dark:stroke-indigo-400'
										/>
										<Box x={170} y={20} w={120} h={40} label='Trace' />
										<Box
											x={170}
											y={70}
											w={120}
											h={40}
											label='Metrics'
											title='Counters and timers for each stage'
											fill='fill-emerald-50 dark:fill-emerald-950'
											stroke='stroke-emerald-600 dark:stroke-emerald-400'
										/>
										<Box
											x={170}
											y={120}
											w={120}
											h={40}
											label='Events'
											title='Structured logs for audits'
											fill='fill-amber-50 dark:fill-amber-950'
											stroke='stroke-amber-600 dark:stroke-amber-400'
										/>
										<Arrow d='M 140 40 L 170 40' />
										<Arrow
											d='M 140 40 C 150 60 150 80 170 90'
											tone='stroke-emerald-600'
										/>
										<Arrow
											d='M 140 40 C 150 100 150 120 170 140'
											tone='stroke-amber-600'
										/>
									</svg>
								</div>
							</div>
							<Separator className='my-4' />
							<div className='text-xs md:text-sm font-mono'>
								<code>{'/traces/{request_id}'}</code> → prompt, memory
								injection, chunk IDs with citations
							</div>
						</CardContent>
					</Card>
				</Section>

				<footer className='pt-6 text-center text-xs text-muted-foreground'>
					© {year} Selfrag — Coordinator focus
				</footer>
			</main>
		</div>
	);
}
