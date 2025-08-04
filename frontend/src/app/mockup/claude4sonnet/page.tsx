// claude 4 sonnet

'use client';

import React, { useState } from 'react';
import {
	MessageSquare,
	FileText,
	Brain,
	Bot,
	Search,
	BarChart3,
	Home,
	Send,
	Upload,
	Filter,
	Clock,
	Tag,
	ExternalLink,
	Eye,
	Settings,
	ChevronRight,
	Zap,
	Database,
	Activity,
	FileSearch,
	MemoryStick, // <-- Use MemoryStick instead of Memory
	Cpu,
	TrendingUp,
	Calendar,
	User,
	Moon,
	Sun,
	MoreVertical,
	Play,
	Pause,
	CheckCircle,
	AlertCircle,
	Info,
	Code,
	GitBranch,
	Target,
} from 'lucide-react';

type Module =
	| 'overview'
	| 'chat'
	| 'rag'
	| 'memory'
	| 'agents'
	| 'inspector'
	| 'analytics';

interface ChatMessage {
	id: string;
	type: 'user' | 'assistant';
	content: string;
	timestamp: string;
	sources?: {
		type: 'rag' | 'memory' | 'model';
		items: string[];
		confidence?: number;
	};
}

interface Document {
	id: string;
	name: string;
	type: string;
	size: string;
	uploadDate: string;
	status: 'processed' | 'processing' | 'failed';
	tags: string[];
}

interface MemoryEntry {
	id: string;
	content: string;
	topic: string;
	timestamp: string;
	relevance: number;
	cluster: string;
}

interface Agent {
	id: string;
	name: string;
	description: string;
	status: 'active' | 'idle' | 'error';
	lastUsed: string;
	tools: string[];
}

export default function SelfragUI() {
	const [activeModule, setActiveModule] = useState<Module>('overview');
	const [darkMode, setDarkMode] = useState(true);
	const [chatInput, setChatInput] = useState('');
	const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
	const [selectedMemory, setSelectedMemory] = useState<string | null>(null);

	const modules = [
		{ id: 'overview' as Module, label: 'Overview', icon: Home },
		{ id: 'chat' as Module, label: 'Chat', icon: MessageSquare },
		{ id: 'rag' as Module, label: 'RAG', icon: FileText },
		{ id: 'memory' as Module, label: 'Memory', icon: Brain },
		{ id: 'agents' as Module, label: 'Agents', icon: Bot },
		{ id: 'inspector' as Module, label: 'Inspector', icon: Search },
		{ id: 'analytics' as Module, label: 'Analytics', icon: BarChart3 },
	];

	const chatMessages: ChatMessage[] = [
		{
			id: '1',
			type: 'user',
			content: 'What are the key insights from the latest research papers?',
			timestamp: '2:30 PM',
		},
		{
			id: '2',
			type: 'assistant',
			content:
				'Based on the research papers in your knowledge base, here are the key insights: 1) Transformer architectures continue to show improvements in efficiency, 2) Multi-modal approaches are becoming more prevalent, 3) Fine-tuning strategies are evolving towards more parameter-efficient methods.',
			timestamp: '2:31 PM',
			sources: {
				type: 'rag',
				items: ['AI_Research_2024.pdf', 'Transformer_Efficiency.pdf'],
				confidence: 0.92,
			},
		},
	];

	const documents: Document[] = [
		{
			id: '1',
			name: 'AI_Research_2024.pdf',
			type: 'PDF',
			size: '2.4 MB',
			uploadDate: '2024-01-15',
			status: 'processed',
			tags: ['research', 'ai', '2024'],
		},
		{
			id: '2',
			name: 'Company_Guidelines.txt',
			type: 'TXT',
			size: '156 KB',
			uploadDate: '2024-01-14',
			status: 'processing',
			tags: ['guidelines', 'internal'],
		},
	];

	const memoryEntries: MemoryEntry[] = [
		{
			id: '1',
			content:
				'User frequently asks about transformer architectures and efficiency improvements',
			topic: 'AI Research Interests',
			timestamp: '2024-01-15 14:30',
			relevance: 0.95,
			cluster: 'Technical Preferences',
		},
		{
			id: '2',
			content: 'Prefers detailed explanations with source citations',
			topic: 'Communication Style',
			timestamp: '2024-01-15 14:25',
			relevance: 0.88,
			cluster: 'User Behavior',
		},
	];

	const agents: Agent[] = [
		{
			id: '1',
			name: 'Research Assistant',
			description: 'Analyzes academic papers and extracts key insights',
			status: 'active',
			lastUsed: '5 minutes ago',
			tools: ['pdf_parser', 'citation_extractor', 'summary_generator'],
		},
		{
			id: '2',
			name: 'Code Analyzer',
			description: 'Reviews and explains code repositories',
			status: 'idle',
			lastUsed: '2 hours ago',
			tools: ['ast_parser', 'complexity_analyzer', 'documentation_generator'],
		},
	];

	const baseClasses = darkMode
		? 'bg-gray-900 text-white'
		: 'bg-white text-gray-900';

	const panelClasses = darkMode
		? 'bg-gray-800 border-gray-700'
		: 'bg-gray-50 border-gray-200';

	const renderLeftPanel = () => {
		switch (activeModule) {
			case 'overview':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold text-lg'>Quick Access</h3>
						<div className='space-y-2'>
							{[
								'Recent Chats',
								'Active Documents',
								'Memory Clusters',
								'Running Agents',
							].map(item => (
								<div
									key={item}
									className={`p-3 rounded-lg border ${panelClasses} hover:bg-opacity-80 cursor-pointer`}
								>
									<span className='text-sm'>{item}</span>
								</div>
							))}
						</div>
					</div>
				);

			case 'chat':
				return (
					<div className='p-4 space-y-4'>
						<div className='relative'>
							<Search className='absolute left-3 top-3 h-4 w-4 text-gray-400' />
							<input
								type='text'
								placeholder='Search conversations...'
								className={`w-full pl-10 pr-4 py-2 rounded-lg border ${panelClasses} focus:outline-none focus:ring-2 focus:ring-blue-500`}
							/>
						</div>

						<div className='space-y-2'>
							<h3 className='font-semibold'>Recent Conversations</h3>
							{[
								'AI Research Discussion',
								'Code Review Session',
								'Memory Analysis',
							].map((conv, idx) => (
								<div
									key={idx}
									className={`p-3 rounded-lg border ${panelClasses} hover:bg-opacity-80 cursor-pointer`}
								>
									<div className='flex items-center gap-2'>
										<MessageSquare className='h-4 w-4' />
										<span className='text-sm'>{conv}</span>
									</div>
									<div className='text-xs text-gray-500 mt-1'>2 hours ago</div>
								</div>
							))}
						</div>

						<div className='space-y-2'>
							<h3 className='font-semibold'>Tags</h3>
							<div className='flex flex-wrap gap-2'>
								{['research', 'coding', 'analysis'].map(tag => (
									<span
										key={tag}
										className='px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs'
									>
										{tag}
									</span>
								))}
							</div>
						</div>
					</div>
				);

			case 'rag':
				return (
					<div className='p-4 space-y-4'>
						<div className='flex items-center gap-2 mb-4'>
							<Filter className='h-4 w-4' />
							<span className='font-semibold'>Filters</span>
						</div>

						<div className='space-y-3'>
							<div>
								<label className='text-sm font-medium'>Format</label>
								<select
									className={`w-full mt-1 p-2 rounded border ${panelClasses}`}
								>
									<option>All formats</option>
									<option>PDF</option>
									<option>TXT</option>
									<option>DOCX</option>
								</select>
							</div>

							<div>
								<label className='text-sm font-medium'>Date Range</label>
								<input
									type='date'
									className={`w-full mt-1 p-2 rounded border ${panelClasses}`}
								/>
							</div>
						</div>

						<div className='space-y-2'>
							<h3 className='font-semibold'>Documents</h3>
							{documents.map(doc => (
								<div
									key={doc.id}
									onClick={() => setSelectedDocument(doc.id)}
									className={`p-3 rounded-lg border cursor-pointer transition-colors ${
										selectedDocument === doc.id
											? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
											: panelClasses
									}`}
								>
									<div className='flex items-center gap-2'>
										<FileText className='h-4 w-4' />
										<span className='text-sm font-medium'>{doc.name}</span>
									</div>
									<div className='text-xs text-gray-500 mt-1'>
										{doc.size} • {doc.uploadDate}
									</div>
									<div className='flex gap-1 mt-2'>
										{doc.tags.map(tag => (
											<span
												key={tag}
												className='px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs'
											>
												{tag}
											</span>
										))}
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'memory':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Memory Clusters</h3>
						<div className='space-y-2'>
							{[
								'Technical Preferences',
								'User Behavior',
								'Domain Knowledge',
							].map(cluster => (
								<div
									key={cluster}
									className={`p-3 rounded-lg border ${panelClasses} cursor-pointer`}
								>
									<div className='flex items-center gap-2'>
										<Brain className='h-4 w-4' />
										<span className='text-sm'>{cluster}</span>
									</div>
								</div>
							))}
						</div>

						<h3 className='font-semibold'>Timeline</h3>
						<div className='space-y-2'>
							{memoryEntries.map(entry => (
								<div
									key={entry.id}
									onClick={() => setSelectedMemory(entry.id)}
									className={`p-3 rounded-lg border cursor-pointer ${
										selectedMemory === entry.id
											? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
											: panelClasses
									}`}
								>
									<div className='text-sm font-medium'>{entry.topic}</div>
									<div className='text-xs text-gray-500'>{entry.timestamp}</div>
									<div className='flex items-center gap-2 mt-1'>
										<div className='w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1'>
											<div
												className='bg-blue-500 h-1 rounded-full'
												style={{ width: `${entry.relevance * 100}%` }}
											></div>
										</div>
										<span className='text-xs'>
											{Math.round(entry.relevance * 100)}%
										</span>
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'agents':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Available Agents</h3>
						<div className='space-y-3'>
							{agents.map(agent => (
								<div
									key={agent.id}
									className={`p-4 rounded-lg border ${panelClasses}`}
								>
									<div className='flex items-center justify-between mb-2'>
										<span className='font-medium'>{agent.name}</span>
										<div
											className={`w-2 h-2 rounded-full ${
												agent.status === 'active'
													? 'bg-green-500'
													: agent.status === 'idle'
													? 'bg-yellow-500'
													: 'bg-red-500'
											}`}
										></div>
									</div>
									<p className='text-sm text-gray-600 dark:text-gray-400 mb-2'>
										{agent.description}
									</p>
									<div className='text-xs text-gray-500'>
										Last used: {agent.lastUsed}
									</div>
									<div className='flex flex-wrap gap-1 mt-2'>
										{agent.tools.map(tool => (
											<span
												key={tool}
												className='px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded text-xs'
											>
												{tool}
											</span>
										))}
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'inspector':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Evaluation Items</h3>
						<div className='space-y-2'>
							{[
								'Retrieved Documents',
								'Agent Steps',
								'Memory Activations',
								'Model Responses',
							].map(item => (
								<div
									key={item}
									className={`p-3 rounded-lg border ${panelClasses} cursor-pointer`}
								>
									<div className='flex items-center gap-2'>
										<Eye className='h-4 w-4' />
										<span className='text-sm'>{item}</span>
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'analytics':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Filters</h3>
						<div className='space-y-3'>
							<div>
								<label className='text-sm font-medium'>Time Range</label>
								<select
									className={`w-full mt-1 p-2 rounded border ${panelClasses}`}
								>
									<option>Last 7 days</option>
									<option>Last 30 days</option>
									<option>Last 90 days</option>
								</select>
							</div>

							<div>
								<label className='text-sm font-medium'>Module</label>
								<select
									className={`w-full mt-1 p-2 rounded border ${panelClasses}`}
								>
									<option>All modules</option>
									<option>Chat</option>
									<option>RAG</option>
									<option>Memory</option>
									<option>Agents</option>
								</select>
							</div>
						</div>
					</div>
				);

			default:
				return null;
		}
	};

	const renderCenterPanel = () => {
		switch (activeModule) {
			case 'overview':
				return (
					<div className='p-6 space-y-6'>
						<h2 className='text-2xl font-bold'>Selfrag Overview</h2>

						<div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
							{[
								{
									label: 'Total Conversations',
									value: '1,234',
									icon: MessageSquare,
								},
								{ label: 'Documents Indexed', value: '45', icon: FileText },
								{ label: 'Memory Entries', value: '892', icon: Brain },
								{ label: 'Active Agents', value: '3', icon: Bot },
							].map((stat, idx) => (
								<div
									key={idx}
									className={`p-4 rounded-lg border ${panelClasses}`}
								>
									<div className='flex items-center gap-3'>
										<stat.icon className='h-8 w-8 text-blue-500' />
										<div>
											<div className='text-2xl font-bold'>{stat.value}</div>
											<div className='text-sm text-gray-500'>{stat.label}</div>
										</div>
									</div>
								</div>
							))}
						</div>

						<div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-semibold mb-4'>Recent Activity</h3>
								<div className='space-y-3'>
									{[
										{
											action: 'New document processed',
											time: '5 min ago',
											icon: FileText,
										},
										{
											action: 'Memory cluster updated',
											time: '15 min ago',
											icon: Brain,
										},
										{
											action: 'Agent task completed',
											time: '1 hour ago',
											icon: Bot,
										},
									].map((activity, idx) => (
										<div key={idx} className='flex items-center gap-3'>
											<activity.icon className='h-4 w-4 text-gray-500' />
											<div className='flex-1'>
												<div className='text-sm'>{activity.action}</div>
												<div className='text-xs text-gray-500'>
													{activity.time}
												</div>
											</div>
										</div>
									))}
								</div>
							</div>

							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-semibold mb-4'>Usage Snapshot</h3>
								<div className='space-y-3'>
									<div className='flex justify-between items-center'>
										<span className='text-sm'>Chat Queries</span>
										<span className='font-medium'>156 today</span>
									</div>
									<div className='flex justify-between items-center'>
										<span className='text-sm'>RAG Retrievals</span>
										<span className='font-medium'>89 today</span>
									</div>
									<div className='flex justify-between items-center'>
										<span className='text-sm'>Memory Activations</span>
										<span className='font-medium'>234 today</span>
									</div>
								</div>
							</div>
						</div>
					</div>
				);

			case 'chat':
				return (
					<div className='flex flex-col h-full'>
						<div className='border-b border-gray-200 dark:border-gray-700 p-4'>
							<h2 className='text-lg font-semibold'>Chat Interface</h2>
							<p className='text-sm text-gray-500'>
								Universal interface for all AI interactions
							</p>
						</div>

						<div className='flex-1 overflow-y-auto p-4 space-y-4'>
							{chatMessages.map(message => (
								<div
									key={message.id}
									className={`flex ${
										message.type === 'user' ? 'justify-end' : 'justify-start'
									}`}
								>
									<div
										className={`max-w-3xl rounded-lg p-4 ${
											message.type === 'user'
												? 'bg-blue-600 text-white'
												: `border ${panelClasses}`
										}`}
									>
										<p className='text-sm'>{message.content}</p>
										<div className='flex items-center justify-between mt-2'>
											<span className='text-xs opacity-70'>
												{message.timestamp}
											</span>
											{message.sources && (
												<div className='flex items-center gap-2'>
													<span
														className={`text-xs px-2 py-1 rounded ${
															message.sources.type === 'rag'
																? 'bg-green-100 text-green-800'
																: message.sources.type === 'memory'
																? 'bg-purple-100 text-purple-800'
																: 'bg-gray-100 text-gray-800'
														}`}
													>
														{message.sources.type.toUpperCase()}
													</span>
													{message.sources.confidence && (
														<span className='text-xs opacity-70'>
															{Math.round(message.sources.confidence * 100)}%
														</span>
													)}
												</div>
											)}
										</div>
									</div>
								</div>
							))}
						</div>

						<div className='border-t border-gray-200 dark:border-gray-700 p-4'>
							<div className='flex gap-2'>
								<textarea
									value={chatInput}
									onChange={e => setChatInput(e.target.value)}
									placeholder='Ask anything... (supports multi-line input)'
									className={`flex-1 p-3 rounded-lg border resize-none ${panelClasses} focus:outline-none focus:ring-2 focus:ring-blue-500`}
									rows={3}
								/>
								<button className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors'>
									<Send className='h-4 w-4' />
								</button>
							</div>
						</div>
					</div>
				);

			case 'rag':
				return (
					<div className='p-6 space-y-6'>
						<div className='border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center'>
							<Upload className='h-12 w-12 text-gray-400 mx-auto mb-4' />
							<p className='text-lg font-medium mb-2'>Upload Documents</p>
							<p className='text-gray-500'>
								Drag and drop files here or click to browse
							</p>
						</div>

						<div className='space-y-4'>
							<h3 className='text-lg font-semibold'>Document Explorer</h3>
							<div className='grid gap-4'>
								{documents.map(doc => (
									<div
										key={doc.id}
										className={`p-4 rounded-lg border ${panelClasses}`}
									>
										<div className='flex items-center justify-between'>
											<div className='flex items-center gap-3'>
												<FileText className='h-6 w-6 text-blue-500' />
												<div>
													<h4 className='font-medium'>{doc.name}</h4>
													<p className='text-sm text-gray-500'>
														{doc.size} • {doc.uploadDate}
													</p>
												</div>
											</div>
											<div className='flex items-center gap-2'>
												{doc.status === 'processed' && (
													<CheckCircle className='h-4 w-4 text-green-500' />
												)}
												{doc.status === 'processing' && (
													<Activity className='h-4 w-4 text-yellow-500 animate-spin' />
												)}
												{doc.status === 'failed' && (
													<AlertCircle className='h-4 w-4 text-red-500' />
												)}
												<span className='text-sm capitalize'>{doc.status}</span>
											</div>
										</div>
										<div className='flex gap-2 mt-3'>
											{doc.tags.map(tag => (
												<span
													key={tag}
													className='px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs'
												>
													{tag}
												</span>
											))}
										</div>
									</div>
								))}
							</div>
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-3'>Test Query</h4>
							<div className='flex gap-2'>
								<input
									type='text'
									placeholder='Test a query against selected documents...'
									className={`flex-1 p-2 rounded border ${panelClasses} focus:outline-none focus:ring-2 focus:ring-blue-500`}
								/>
								<button className='bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700'>
									<Search className='h-4 w-4' />
								</button>
							</div>
						</div>
					</div>
				);

			case 'memory':
				return (
					<div className='p-6 space-y-6'>
						<h2 className='text-xl font-semibold'>Memory Explorer</h2>

						<div className='grid gap-4'>
							{memoryEntries.map(entry => (
								<div
									key={entry.id}
									className={`p-4 rounded-lg border ${panelClasses}`}
								>
									<div className='flex items-start justify-between'>
										<div className='flex-1'>
											<h4 className='font-medium mb-2'>{entry.topic}</h4>
											<p className='text-sm text-gray-600 dark:text-gray-400 mb-3'>
												{entry.content}
											</p>
											<div className='flex items-center gap-4 text-xs text-gray-500'>
												<span>{entry.timestamp}</span>
												<span>Cluster: {entry.cluster}</span>
											</div>
										</div>
										<div className='flex items-center gap-2 ml-4'>
											<div className='text-right'>
												<div className='text-sm font-medium'>
													{Math.round(entry.relevance * 100)}%
												</div>
												<div className='text-xs text-gray-500'>relevance</div>
											</div>
											<div className='w-2 h-8 bg-gray-200 dark:bg-gray-700 rounded-full'>
												<div
													className='bg-blue-500 rounded-full w-full'
													style={{ height: `${entry.relevance * 100}%` }}
												></div>
											</div>
										</div>
									</div>
								</div>
							))}
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-3'>Memory Interaction</h4>
							<div className='flex gap-2'>
								<input
									type='text'
									placeholder='Query memory entries...'
									className={`flex-1 p-2 rounded border ${panelClasses} focus:outline-none focus:ring-2 focus:ring-blue-500`}
								/>
								<button className='bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700'>
									<Brain className='h-4 w-4' />
								</button>
							</div>
						</div>
					</div>
				);

			case 'agents':
				return (
					<div className='p-6 space-y-6'>
						<h2 className='text-xl font-semibold'>Agent Output Canvas</h2>

						<div className='grid gap-6'>
							{agents.map(agent => (
								<div
									key={agent.id}
									className={`p-6 rounded-lg border ${panelClasses}`}
								>
									<div className='flex items-center justify-between mb-4'>
										<div className='flex items-center gap-3'>
											<Bot className='h-6 w-6 text-purple-500' />
											<div>
												<h3 className='font-semibold'>{agent.name}</h3>
												<p className='text-sm text-gray-500'>
													{agent.description}
												</p>
											</div>
										</div>
										<div className='flex items-center gap-2'>
											<div
												className={`w-3 h-3 rounded-full ${
													agent.status === 'active'
														? 'bg-green-500'
														: agent.status === 'idle'
														? 'bg-yellow-500'
														: 'bg-red-500'
												}`}
											></div>
											<span className='text-sm capitalize'>{agent.status}</span>
										</div>
									</div>

									<div className='space-y-3'>
										<h4 className='font-medium'>Recent Tasks</h4>
										<div className='space-y-2'>
											{[
												'Analyzed research paper structure',
												'Extracted key citations',
												'Generated summary',
											].map((task, idx) => (
												<div
													key={idx}
													className='flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded'
												>
													<CheckCircle className='h-4 w-4 text-green-500' />
													<span className='text-sm'>{task}</span>
												</div>
											))}
										</div>
									</div>

									<div className='mt-4 pt-4 border-t border-gray-200 dark:border-gray-700'>
										<button className='bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors'>
											<Play className='h-4 w-4 inline mr-2' />
											Trigger Agent
										</button>
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'inspector':
				return (
					<div className='p-6 space-y-6'>
						<h2 className='text-xl font-semibold'>Reasoning Trace Viewer</h2>

						<div className='space-y-4'>
							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-medium mb-3'>Trace Timeline</h3>
								<div className='space-y-3'>
									{[
										{
											step: 'Query received',
											time: '14:30:01',
											status: 'completed',
										},
										{
											step: 'RAG retrieval initiated',
											time: '14:30:02',
											status: 'completed',
										},
										{
											step: 'Memory activation',
											time: '14:30:03',
											status: 'completed',
										},
										{
											step: 'Response generation',
											time: '14:30:04',
											status: 'in-progress',
										},
									].map((trace, idx) => (
										<div key={idx} className='flex items-center gap-3'>
											<div
												className={`w-3 h-3 rounded-full ${
													trace.status === 'completed'
														? 'bg-green-500'
														: trace.status === 'in-progress'
														? 'bg-yellow-500'
														: 'bg-gray-300'
												}`}
											></div>
											<div className='flex-1'>
												<span className='text-sm'>{trace.step}</span>
												<span className='text-xs text-gray-500 ml-2'>
													{trace.time}
												</span>
											</div>
										</div>
									))}
								</div>
							</div>

							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-medium mb-3'>Decision Points</h3>
								<div className='space-y-2'>
									<div className='p-3 bg-blue-50 dark:bg-blue-900 rounded'>
										<div className='text-sm font-medium'>RAG Threshold Met</div>
										<div className='text-xs text-gray-600 dark:text-gray-400'>
											Confidence: 0.92 {'>'} 0.8 threshold
										</div>
									</div>
									<div className='p-3 bg-purple-50 dark:bg-purple-900 rounded'>
										<div className='text-sm font-medium'>Memory Activated</div>
										<div className='text-xs text-gray-600 dark:text-gray-400'>
											User preference pattern matched
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				);

			case 'analytics':
				return (
					<div className='p-6 space-y-6'>
						<h2 className='text-xl font-semibold'>Analytics Dashboard</h2>

						<div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-medium mb-3'>Usage by Module</h3>
								<div className='space-y-2'>
									{[
										{ module: 'Chat', usage: 45, color: 'bg-blue-500' },
										{ module: 'RAG', usage: 30, color: 'bg-green-500' },
										{ module: 'Memory', usage: 20, color: 'bg-purple-500' },
										{ module: 'Agents', usage: 5, color: 'bg-orange-500' },
									].map(item => (
										<div key={item.module} className='flex items-center gap-3'>
											<div
												className={`w-3 h-3 rounded-full ${item.color}`}
											></div>
											<span className='text-sm flex-1'>{item.module}</span>
											<span className='text-sm font-medium'>{item.usage}%</span>
										</div>
									))}
								</div>
							</div>

							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-medium mb-3'>Response Times</h3>
								<div className='space-y-2'>
									<div className='flex justify-between'>
										<span className='text-sm'>Average</span>
										<span className='font-medium'>1.2s</span>
									</div>
									<div className='flex justify-between'>
										<span className='text-sm'>P95</span>
										<span className='font-medium'>2.8s</span>
									</div>
									<div className='flex justify-between'>
										<span className='text-sm'>P99</span>
										<span className='font-medium'>4.1s</span>
									</div>
								</div>
							</div>

							<div className={`p-4 rounded-lg border ${panelClasses}`}>
								<h3 className='font-medium mb-3'>Success Rates</h3>
								<div className='space-y-2'>
									<div className='flex justify-between'>
										<span className='text-sm'>Overall</span>
										<span className='font-medium text-green-600'>94.2%</span>
									</div>
									<div className='flex justify-between'>
										<span className='text-sm'>RAG Retrieval</span>
										<span className='font-medium text-green-600'>96.8%</span>
									</div>
									<div className='flex justify-between'>
										<span className='text-sm'>Agent Tasks</span>
										<span className='font-medium text-yellow-600'>87.3%</span>
									</div>
								</div>
							</div>
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h3 className='font-medium mb-3'>Topic Drift Analysis</h3>
							<div className='h-32 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center'>
								<span className='text-gray-500'>
									Chart visualization would go here
								</span>
							</div>
						</div>
					</div>
				);

			default:
				return null;
		}
	};

	const renderRightPanel = () => {
		switch (activeModule) {
			case 'overview':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>System Status</h3>
						<div className='space-y-3'>
							{[
								{ service: 'LLM API', status: 'online', latency: '120ms' },
								{ service: 'Vector DB', status: 'online', latency: '45ms' },
								{ service: 'Memory Store', status: 'online', latency: '23ms' },
							].map(service => (
								<div
									key={service.service}
									className={`p-3 rounded-lg border ${panelClasses}`}
								>
									<div className='flex items-center justify-between'>
										<span className='text-sm'>{service.service}</span>
										<div className='flex items-center gap-2'>
											<div className='w-2 h-2 bg-green-500 rounded-full'></div>
											<span className='text-xs'>{service.latency}</span>
										</div>
									</div>
								</div>
							))}
						</div>
					</div>
				);

			case 'chat':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Live Influences</h3>

						<div className='space-y-3'>
							<div className={`p-3 rounded-lg border ${panelClasses}`}>
								<h4 className='text-sm font-medium mb-2'>Memory Highlights</h4>
								<div className='space-y-2'>
									<div className='text-xs text-gray-600 dark:text-gray-400'>
										• User prefers detailed explanations
									</div>
									<div className='text-xs text-gray-600 dark:text-gray-400'>
										• Interested in AI research topics
									</div>
								</div>
							</div>

							<div className={`p-3 rounded-lg border ${panelClasses}`}>
								<h4 className='text-sm font-medium mb-2'>Document Citations</h4>
								<div className='space-y-2'>
									{['AI_Research_2024.pdf', 'Transformer_Efficiency.pdf'].map(
										doc => (
											<div key={doc} className='flex items-center gap-2'>
												<ExternalLink className='h-3 w-3' />
												<span className='text-xs'>{doc}</span>
											</div>
										),
									)}
								</div>
							</div>

							<div className={`p-3 rounded-lg border ${panelClasses}`}>
								<h4 className='text-sm font-medium mb-2'>
									Response Confidence
								</h4>
								<div className='flex items-center gap-2'>
									<div className='flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2'>
										<div className='bg-green-500 h-2 rounded-full w-11/12'></div>
									</div>
									<span className='text-xs'>92%</span>
								</div>
							</div>
						</div>
					</div>
				);

			case 'rag':
				return (
					<div className='p-4 space-y-4'>
						{selectedDocument ? (
							<>
								<h3 className='font-semibold'>Document Preview</h3>
								<div className={`p-4 rounded-lg border ${panelClasses}`}>
									<h4 className='font-medium mb-2'>AI_Research_2024.pdf</h4>
									<div className='text-sm text-gray-600 dark:text-gray-400 space-y-2'>
										<p>
											This paper presents novel approaches to transformer
											architecture optimization...
										</p>
										<p>
											Key findings include a 23% improvement in processing
											efficiency...
										</p>
									</div>
								</div>

								<h4 className='font-medium'>Metadata</h4>
								<div className='space-y-2 text-sm'>
									<div className='flex justify-between'>
										<span>Size:</span>
										<span>2.4 MB</span>
									</div>
									<div className='flex justify-between'>
										<span>Pages:</span>
										<span>24</span>
									</div>
									<div className='flex justify-between'>
										<span>Chunks:</span>
										<span>156</span>
									</div>
								</div>

								<h4 className='font-medium'>Matching Chunks</h4>
								<div className='space-y-2'>
									<div className={`p-2 rounded border ${panelClasses} text-xs`}>
										"Transformer models demonstrate significant improvements..."
										<div className='text-gray-500 mt-1'>Relevance: 0.94</div>
									</div>
								</div>
							</>
						) : (
							<div className='text-center text-gray-500 mt-8'>
								<FileSearch className='h-12 w-12 mx-auto mb-4 opacity-50' />
								<p>Select a document to preview</p>
							</div>
						)}
					</div>
				);

			case 'memory':
				return (
					<div className='p-4 space-y-4'>
						{selectedMemory ? (
							<>
								<h3 className='font-semibold'>Memory Details</h3>
								<div className={`p-4 rounded-lg border ${panelClasses}`}>
									<h4 className='font-medium mb-2'>Technical Preferences</h4>
									<p className='text-sm text-gray-600 dark:text-gray-400 mb-3'>
										User frequently asks about transformer architectures and
										efficiency improvements
									</p>
									<div className='space-y-2 text-xs'>
										<div className='flex justify-between'>
											<span>Cluster:</span>
											<span>Technical Preferences</span>
										</div>
										<div className='flex justify-between'>
											<span>Relevance:</span>
											<span>95%</span>
										</div>
										<div className='flex justify-between'>
											<span>Last Updated:</span>
											<span>2024-01-15 14:30</span>
										</div>
									</div>
								</div>

								<h4 className='font-medium'>Extraction Summary</h4>
								<div
									className={`p-3 rounded-lg border ${panelClasses} text-sm`}
								>
									<p className='text-gray-600 dark:text-gray-400'>
										Extracted from 12 conversations over the past week. Pattern
										shows consistent interest in AI efficiency metrics.
									</p>
								</div>
							</>
						) : (
							<div className='text-center text-gray-500 mt-8'>
								<MemoryStick className='h-12 w-12 mx-auto mb-4 opacity-50' />
								<p>Select a memory entry to view details</p>
							</div>
						)}
					</div>
				);

			case 'agents':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Agent Parameters</h3>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-3'>Research Assistant</h4>
							<div className='space-y-3'>
								<div>
									<label className='text-sm font-medium'>Max Tokens</label>
									<input
										type='number'
										value='2048'
										className={`w-full mt-1 p-2 rounded border ${panelClasses}`}
									/>
								</div>
								<div>
									<label className='text-sm font-medium'>Temperature</label>
									<input
										type='range'
										min='0'
										max='1'
										step='0.1'
										value='0.3'
										className='w-full mt-1'
									/>
								</div>
							</div>
						</div>

						<h4 className='font-medium'>Trace Info</h4>
						<div className='space-y-2 text-sm'>
							<div className='flex justify-between'>
								<span>Status:</span>
								<span className='text-green-600'>Active</span>
							</div>
							<div className='flex justify-between'>
								<span>Last Task:</span>
								<span>5 min ago</span>
							</div>
							<div className='flex justify-between'>
								<span>Success Rate:</span>
								<span>94.2%</span>
							</div>
						</div>

						<h4 className='font-medium'>YAML Config</h4>
						<div
							className={`p-3 rounded border ${panelClasses} text-xs font-mono`}
						>
							<pre className='text-gray-600 dark:text-gray-400'>
								{`name: research_assistant
tools:
  - pdf_parser
  - citation_extractor
  - summary_generator
parameters:
  max_tokens: 2048
  temperature: 0.3`}
							</pre>
						</div>
					</div>
				);

			case 'inspector':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Source Expansion</h3>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-2'>Token View</h4>
							<div className='text-xs font-mono space-y-1'>
								<div>
									Input tokens: <span className='font-bold'>156</span>
								</div>
								<div>
									Output tokens: <span className='font-bold'>89</span>
								</div>
								<div>
									Total cost: <span className='font-bold'>$0.0023</span>
								</div>
							</div>
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-2'>Raw Document</h4>
							<div className='text-xs text-gray-600 dark:text-gray-400 max-h-32 overflow-y-auto'>
								<p>
									This paper presents novel approaches to transformer
									architecture optimization. The key innovation lies in the
									attention mechanism refinement...
								</p>
							</div>
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-2'>Trace Log</h4>
							<div className='text-xs font-mono space-y-1 max-h-32 overflow-y-auto'>
								<div>[14:30:01] Query received</div>
								<div>[14:30:02] RAG retrieval: 0.92 confidence</div>
								<div>[14:30:03] Memory activated: user_preferences</div>
								<div>[14:30:04] Response generated</div>
							</div>
						</div>
					</div>
				);

			case 'analytics':
				return (
					<div className='p-4 space-y-4'>
						<h3 className='font-semibold'>Explanations</h3>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-2'>Usage Patterns</h4>
							<p className='text-sm text-gray-600 dark:text-gray-400'>
								Chat module shows highest usage during business hours (9-17
								UTC). RAG retrievals peak when processing new documents.
							</p>
						</div>

						<div className={`p-4 rounded-lg border ${panelClasses}`}>
							<h4 className='font-medium mb-2'>Performance Insights</h4>
							<p className='text-sm text-gray-600 dark:text-gray-400'>
								Response times have improved 15% over the past week due to
								memory optimization. Agent success rates vary by task
								complexity.
							</p>
						</div>

						<h4 className='font-medium'>Module Statistics</h4>
						<div className='space-y-2 text-sm'>
							<div className='flex justify-between'>
								<span>Total Queries:</span>
								<span>1,234</span>
							</div>
							<div className='flex justify-between'>
								<span>Avg Daily Usage:</span>
								<span>156 queries</span>
							</div>
							<div className='flex justify-between'>
								<span>Peak Hour:</span>
								<span>14:00-15:00</span>
							</div>
						</div>
					</div>
				);

			default:
				return null;
		}
	};

	return (
		<div className={`h-screen flex ${baseClasses}`}>
			{/* Left Panel - Navigation */}
			<div className={`w-64 border-r ${panelClasses} flex flex-col`}>
				{/* Header */}
				<div className='p-4 border-b border-gray-200 dark:border-gray-700'>
					<div className='flex items-center justify-between'>
						<h1 className='text-xl font-bold'>Selfrag</h1>
						<button
							onClick={() => setDarkMode(!darkMode)}
							className='p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700'
						>
							{darkMode ? (
								<Sun className='h-4 w-4' />
							) : (
								<Moon className='h-4 w-4' />
							)}
						</button>
					</div>
				</div>

				{/* Navigation */}
				<nav className='flex-1 p-4'>
					<ul className='space-y-2'>
						{modules.map(module => {
							const Icon = module.icon;
							return (
								<li key={module.id}>
									<button
										onClick={() => setActiveModule(module.id)}
										className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
											activeModule === module.id
												? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
												: 'hover:bg-gray-100 dark:hover:bg-gray-700'
										}`}
									>
										<Icon className='h-5 w-5' />
										<span className='font-medium'>{module.label}</span>
									</button>
								</li>
							);
						})}
					</ul>
				</nav>

				{/* Module-specific left content */}
				<div className='border-t border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto'>
					{renderLeftPanel()}
				</div>
			</div>

			{/* Center Panel - Main Content */}
			<div className='flex-1 flex flex-col'>
				<main className='flex-1 overflow-hidden'>{renderCenterPanel()}</main>
			</div>

			{/* Right Panel - Context/Details */}
			<div className={`w-80 border-l ${panelClasses} overflow-y-auto`}>
				{renderRightPanel()}
			</div>
		</div>
	);
}
