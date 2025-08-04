'use client';

import { useState } from 'react';
import {
	MessageSquare,
	Search,
	FileText,
	Brain,
	Bot,
	Eye,
	BarChart3,
	Home,
	ChevronLeft,
	ChevronRight,
	Send,
	Plus,
	Upload,
	Settings,
	User,
	Maximize2,
	Minimize2,
} from 'lucide-react';

// Define types for our data structures
type Message = {
	id: string;
	content: string;
	role: 'user' | 'assistant';
	timestamp: Date;
	sources?: string[];
};

type Document = {
	id: string;
	name: string;
	type: string;
	date: Date;
	size: string;
};

type MemoryEntry = {
	id: string;
	title: string;
	content: string;
	timestamp: Date;
	cluster: string;
};

type Agent = {
	id: string;
	name: string;
	description: string;
	status: 'active' | 'inactive';
};

// Mock data
const mockMessages: Message[] = [
	{
		id: '1',
		content: 'Hello, how can I help you today?',
		role: 'assistant',
		timestamp: new Date(),
		sources: ['Memory', 'Model'],
	},
	{
		id: '2',
		content: 'I need information about quantum computing.',
		role: 'user',
		timestamp: new Date(),
	},
	{
		id: '3',
		content:
			'Quantum computing is a type of computation that harnesses quantum mechanical phenomena to process information. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or qubits, which can exist in multiple states simultaneously.',
		role: 'assistant',
		timestamp: new Date(),
		sources: ['RAG: Quantum Computing Guide', 'Model'],
	},
];

const mockDocuments: Document[] = [
	{
		id: '1',
		name: 'Quantum Computing Guide',
		type: 'PDF',
		date: new Date(),
		size: '2.4MB',
	},
	{
		id: '2',
		name: 'AI Research Paper',
		type: 'PDF',
		date: new Date(),
		size: '4.1MB',
	},
	{
		id: '3',
		name: 'Machine Learning Basics',
		type: 'DOCX',
		date: new Date(),
		size: '1.2MB',
	},
];

const mockMemoryEntries: MemoryEntry[] = [
	{
		id: '1',
		title: 'Quantum Basics',
		content: 'Fundamental principles of quantum computing',
		timestamp: new Date(),
		cluster: 'Science',
	},
	{
		id: '2',
		title: 'User Preferences',
		content: 'Prefers detailed explanations with examples',
		timestamp: new Date(),
		cluster: 'Preferences',
	},
];

const mockAgents: Agent[] = [
	{
		id: '1',
		name: 'Research Assistant',
		description: 'Helps with academic research',
		status: 'active',
	},
	{
		id: '2',
		name: 'Code Reviewer',
		description: 'Reviews and improves code',
		status: 'active',
	},
	{
		id: '3',
		name: 'Data Analyst',
		description: 'Analyzes datasets and provides insights',
		status: 'inactive',
	},
];

// Main component
export default function SelfRAGUI() {
	const [activeModule, setActiveModule] = useState<
		| 'chat'
		| 'rag'
		| 'memory'
		| 'agent'
		| 'inspector'
		| 'analytics'
		| 'composite'
	>('chat');
	const [messages, setMessages] = useState<Message[]>(mockMessages);
	const [inputValue, setInputValue] = useState('');
	const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
	const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

	const handleSendMessage = () => {
		if (inputValue.trim() === '') return;

		const newMessage: Message = {
			id: (messages.length + 1).toString(),
			content: inputValue,
			role: 'user',
			timestamp: new Date(),
		};

		setMessages([...messages, newMessage]);
		setInputValue('');

		// Simulate response after a delay
		setTimeout(() => {
			const response: Message = {
				id: (messages.length + 2).toString(),
				content: 'This is a simulated response to your message.',
				role: 'assistant',
				timestamp: new Date(),
				sources: ['Model'],
			};
			setMessages(prev => [...prev, response]);
		}, 1000);
	};

	const renderLeftPanel = () => {
		switch (activeModule) {
			case 'chat':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<button className='w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 rounded-md flex items-center justify-center text-white'>
								<Plus className='h-4 w-4 mr-2' />
								New Chat
							</button>
						</div>
						<div className='p-4'>
							<h3 className='text-sm font-medium text-gray-400 mb-2'>
								Recent Conversations
							</h3>
							<div className='space-y-2'>
								{['Quantum Computing', 'AI Research', 'Project Planning'].map(
									(chat, index) => (
										<div
											key={index}
											className='p-3 rounded-lg hover:bg-gray-800 cursor-pointer'
										>
											<div className='font-medium'>{chat}</div>
											<div className='text-xs text-gray-400'>
												Today, 10:30 AM
											</div>
										</div>
									),
								)}
							</div>
						</div>
					</div>
				);
			case 'rag':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<div className='relative'>
								<Search className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
								<input
									type='text'
									placeholder='Search documents...'
									className='w-full pl-10 pr-4 py-2 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
								/>
							</div>
						</div>
						<div className='p-4'>
							<div className='flex justify-between items-center mb-4'>
								<h3 className='text-sm font-medium text-gray-400'>Documents</h3>
								<div className='text-xs text-gray-400'>3 files</div>
							</div>
							<div className='space-y-2'>
								{mockDocuments.map(doc => (
									<div
										key={doc.id}
										className='p-3 rounded-lg hover:bg-gray-800 cursor-pointer'
									>
										<div className='flex items-center'>
											<FileText className='h-5 w-5 mr-2 text-indigo-400' />
											<div className='font-medium'>{doc.name}</div>
										</div>
										<div className='text-xs text-gray-400 mt-1'>
											{doc.type} • {doc.size}
										</div>
									</div>
								))}
							</div>
						</div>
					</div>
				);
			case 'memory':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<div className='relative'>
								<Search className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
								<input
									type='text'
									placeholder='Search memories...'
									className='w-full pl-10 pr-4 py-2 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
								/>
							</div>
						</div>
						<div className='p-4'>
							<h3 className='text-sm font-medium text-gray-400 mb-2'>
								Memory Clusters
							</h3>
							<div className='space-y-2'>
								{['Science', 'Preferences', 'Projects', 'Personal'].map(
									(cluster, index) => (
										<div
											key={index}
											className='p-3 rounded-lg hover:bg-gray-800 cursor-pointer'
										>
											<div className='font-medium'>{cluster}</div>
											<div className='text-xs text-gray-400'>
												{index + 2} entries
											</div>
										</div>
									),
								)}
							</div>
						</div>
					</div>
				);
			case 'agent':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Available Agents</h3>
						</div>
						<div className='p-4'>
							<div className='space-y-2'>
								{mockAgents.map(agent => (
									<div
										key={agent.id}
										className='p-3 rounded-lg hover:bg-gray-800 cursor-pointer'
									>
										<div className='flex items-center justify-between'>
											<div className='font-medium'>{agent.name}</div>
											<div
												className={`h-2 w-2 rounded-full ${
													agent.status === 'active'
														? 'bg-green-500'
														: 'bg-gray-500'
												}`}
											></div>
										</div>
										<div className='text-xs text-gray-400 mt-1'>
											{agent.description}
										</div>
									</div>
								))}
							</div>
						</div>
					</div>
				);
			case 'inspector':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Evaluated Items</h3>
						</div>
						<div className='p-4'>
							<div className='space-y-2'>
								{[
									'Retrieved Docs',
									'Agent Steps',
									'Reasoning Path',
									'Model Output',
								].map((item, index) => (
									<div
										key={index}
										className='p-3 rounded-lg hover:bg-gray-800 cursor-pointer'
									>
										<div className='font-medium'>{item}</div>
										<div className='text-xs text-gray-400 mt-1'>
											Last evaluated: Today
										</div>
									</div>
								))}
							</div>
						</div>
					</div>
				);
			case 'analytics':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Filter Controls</h3>
						</div>
						<div className='p-4'>
							<div className='space-y-4'>
								<div>
									<h4 className='text-sm font-medium text-gray-400 mb-2'>
										Time Range
									</h4>
									<select className='w-full p-2 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'>
										<option>Last 7 days</option>
										<option>Last 30 days</option>
										<option>Last 90 days</option>
										<option>All time</option>
									</select>
								</div>
								<div>
									<h4 className='text-sm font-medium text-gray-400 mb-2'>
										Topic
									</h4>
									<select className='w-full p-2 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'>
										<option>All topics</option>
										<option>Science</option>
										<option>Technology</option>
										<option>Business</option>
									</select>
								</div>
								<div>
									<h4 className='text-sm font-medium text-gray-400 mb-2'>
										Usage Type
									</h4>
									<select className='w-full p-2 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'>
										<option>All types</option>
										<option>Chat</option>
										<option>RAG</option>
										<option>Memory</option>
										<option>Agents</option>
									</select>
								</div>
							</div>
						</div>
					</div>
				);
			case 'composite':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Dashboard Overview</h3>
						</div>
						<div className='p-4'>
							<div className='space-y-4'>
								<div>
									<h4 className='text-sm font-medium text-gray-400 mb-2'>
										Recent Activity
									</h4>
									<div className='space-y-2'>
										{[
											'Chat about quantum computing',
											'Added new document',
											'Created memory entry',
										].map((activity, index) => (
											<div
												key={index}
												className='p-2 rounded-lg hover:bg-gray-800 cursor-pointer text-sm'
											>
												{activity}
											</div>
										))}
									</div>
								</div>
								<div>
									<h4 className='text-sm font-medium text-gray-400 mb-2'>
										Quick Access
									</h4>
									<div className='grid grid-cols-2 gap-2'>
										{['New Chat', 'Upload Doc', 'View Memory', 'Run Agent'].map(
											(action, index) => (
												<button
													key={index}
													className='p-2 bg-gray-800 hover:bg-gray-700 rounded-md text-sm'
												>
													{action}
												</button>
											),
										)}
									</div>
								</div>
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
			case 'chat':
				return (
					<div className='flex flex-col h-full'>
						<div className='flex-1 overflow-y-auto p-4 space-y-4'>
							{messages.map(message => (
								<div
									key={message.id}
									className={`p-4 rounded-lg max-w-3xl ${
										message.role === 'user'
											? 'bg-indigo-900/30 ml-auto'
											: 'bg-gray-800'
									}`}
								>
									<div className='flex items-start'>
										<div
											className={`h-8 w-8 rounded-full flex items-center justify-center mr-3 ${
												message.role === 'user'
													? 'bg-indigo-600'
													: 'bg-gray-700'
											}`}
										>
											{message.role === 'user' ? (
												<User className='h-4 w-4' />
											) : (
												<Bot className='h-4 w-4' />
											)}
										</div>
										<div className='flex-1'>
											<div className='font-medium mb-1'>
												{message.role === 'user' ? 'You' : 'Assistant'}
											</div>
											<div className='text-gray-300'>{message.content}</div>
											{message.sources && (
												<div className='mt-2 flex flex-wrap gap-1'>
													{message.sources.map((source, index) => (
														<span
															key={index}
															className='text-xs bg-gray-700 px-2 py-1 rounded'
														>
															{source}
														</span>
													))}
												</div>
											)}
										</div>
									</div>
								</div>
							))}
						</div>
						<div className='p-4 border-t border-gray-700'>
							<div className='flex items-center'>
								<textarea
									value={inputValue}
									onChange={e => setInputValue(e.target.value)}
									placeholder='Type your message here...'
									className='flex-1 p-3 bg-gray-800 rounded-l-md focus:outline-none resize-none'
									rows={2}
									onKeyDown={e => {
										if (e.key === 'Enter' && !e.shiftKey) {
											e.preventDefault();
											handleSendMessage();
										}
									}}
								/>
								<button
									onClick={handleSendMessage}
									className='h-full p-3 bg-indigo-600 hover:bg-indigo-700 rounded-r-md'
								>
									<Send className='h-5 w-5' />
								</button>
							</div>
						</div>
					</div>
				);
			case 'rag':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Document Management</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h3 className='text-lg font-medium mb-3'>Upload Documents</h3>
								<div className='border-2 border-dashed border-gray-700 rounded-lg p-8 text-center'>
									<Upload className='h-12 w-12 mx-auto text-gray-500 mb-3' />
									<p className='text-gray-400 mb-2'>
										Drag and drop files here or click to browse
									</p>
									<button className='px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-md'>
										Select Files
									</button>
								</div>
							</div>

							<div>
								<h3 className='text-lg font-medium mb-3'>Document Explorer</h3>
								<div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
									{mockDocuments.map(doc => (
										<div key={doc.id} className='p-4 bg-gray-800 rounded-lg'>
											<div className='flex items-start'>
												<FileText className='h-6 w-6 mr-3 text-indigo-400 mt-1' />
												<div className='flex-1'>
													<div className='font-medium'>{doc.name}</div>
													<div className='text-sm text-gray-400 mt-1'>
														{doc.type} • {doc.size}
													</div>
													<div className='mt-3 text-sm'>
														This document contains information about quantum
														computing principles and applications.
													</div>
												</div>
											</div>
										</div>
									))}
								</div>
							</div>
						</div>
					</div>
				);
			case 'memory':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Memory Explorer</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h3 className='text-lg font-medium mb-3'>Memory Entries</h3>
								<div className='space-y-4'>
									{mockMemoryEntries.map(memory => (
										<div key={memory.id} className='p-4 bg-gray-800 rounded-lg'>
											<div className='flex justify-between items-start mb-2'>
												<div className='font-medium'>{memory.title}</div>
												<span className='text-xs bg-indigo-900/50 px-2 py-1 rounded'>
													{memory.cluster}
												</span>
											</div>
											<div className='text-gray-300'>{memory.content}</div>
											<div className='text-xs text-gray-500 mt-2'>
												{memory.timestamp.toLocaleString()}
											</div>
										</div>
									))}
								</div>
							</div>

							<div>
								<h3 className='text-lg font-medium mb-3'>
									Session-to-Memory Linking
								</h3>
								<div className='p-4 bg-gray-800 rounded-lg'>
									<p className='text-gray-400 mb-3'>
										Link current session to memory clusters
									</p>
									<div className='flex flex-wrap gap-2'>
										{['Science', 'Preferences', 'Projects'].map(
											(cluster, index) => (
												<button
													key={index}
													className='px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-md text-sm'
												>
													{cluster}
												</button>
											),
										)}
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'agent':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Agent Workspace</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h3 className='text-lg font-medium mb-3'>
									Active Agent: Research Assistant
								</h3>
								<div className='p-4 bg-gray-800 rounded-lg'>
									<div className='mb-4'>
										<h4 className='font-medium mb-2'>Task Description</h4>
										<p className='text-gray-300'>
											Research the latest developments in quantum computing and
											provide a summary of key breakthroughs.
										</p>
									</div>

									<div className='mb-4'>
										<h4 className='font-medium mb-2'>Execution Steps</h4>
										<div className='space-y-2'>
											{[
												'Search for recent quantum computing papers',
												'Extract key findings and breakthroughs',
												'Synthesize information into a coherent summary',
												'Format and present the results',
											].map((step, index) => (
												<div
													key={index}
													className='flex items-center p-2 bg-gray-700 rounded'
												>
													<div className='h-5 w-5 rounded-full bg-indigo-600 flex items-center justify-center text-xs mr-2'>
														{index + 1}
													</div>
													<div>{step}</div>
												</div>
											))}
										</div>
									</div>

									<div>
										<h4 className='font-medium mb-2'>Agent Output</h4>
										<div className='p-3 bg-gray-900 rounded text-sm'>
											<p className='text-gray-300 mb-2'>
												Recent breakthroughs in quantum computing include:
											</p>
											<ul className='list-disc pl-5 space-y-1 text-gray-300'>
												<li>
													Error correction improvements reducing qubit
													requirements
												</li>
												<li>New algorithms for quantum machine learning</li>
												<li>Progress in quantum hardware scalability</li>
											</ul>
										</div>
									</div>
								</div>
							</div>

							<div>
								<h3 className='text-lg font-medium mb-3'>Available Agents</h3>
								<div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
									{mockAgents.map(agent => (
										<div key={agent.id} className='p-4 bg-gray-800 rounded-lg'>
											<div className='flex justify-between items-start mb-2'>
												<div className='font-medium'>{agent.name}</div>
												<div
													className={`h-2 w-2 rounded-full ${
														agent.status === 'active'
															? 'bg-green-500'
															: 'bg-gray-500'
													}`}
												></div>
											</div>
											<div className='text-sm text-gray-400 mb-3'>
												{agent.description}
											</div>
											<button className='w-full py-2 bg-indigo-600 hover:bg-indigo-700 rounded-md text-sm'>
												Activate Agent
											</button>
										</div>
									))}
								</div>
							</div>
						</div>
					</div>
				);
			case 'inspector':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Reasoning Inspector</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h3 className='text-lg font-medium mb-3'>Reasoning Trace</h3>
								<div className='p-4 bg-gray-800 rounded-lg'>
									<div className='space-y-4'>
										<div>
											<div className='font-medium mb-1'>Query Analysis</div>
											<div className='text-sm text-gray-300'>
												User asked about quantum computing basics
											</div>
										</div>
										<div>
											<div className='font-medium mb-1'>Memory Retrieval</div>
											<div className='text-sm text-gray-300'>
												Found 2 relevant memory entries about quantum physics
											</div>
										</div>
										<div>
											<div className='font-medium mb-1'>RAG Retrieval</div>
											<div className='text-sm text-gray-300'>
												Retrieved 3 documents about quantum computing
											</div>
										</div>
										<div>
											<div className='font-medium mb-1'>
												Response Generation
											</div>
											<div className='text-sm text-gray-300'>
												Generated response combining retrieved information and
												model knowledge
											</div>
										</div>
									</div>
								</div>
							</div>

							<div>
								<h3 className='text-lg font-medium mb-3'>Evaluation Metrics</h3>
								<div className='grid grid-cols-2 gap-4'>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='text-sm text-gray-400 mb-1'>
											Relevance Score
										</div>
										<div className='text-2xl font-bold text-indigo-400'>
											92%
										</div>
									</div>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='text-sm text-gray-400 mb-1'>
											Confidence Level
										</div>
										<div className='text-2xl font-bold text-green-400'>
											High
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'analytics':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Usage Analytics</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h3 className='text-lg font-medium mb-3'>Activity Overview</h3>
								<div className='p-4 bg-gray-800 rounded-lg'>
									<div className='h-64 flex items-center justify-center text-gray-500'>
										[Chart: Activity over time would be displayed here]
									</div>
								</div>
							</div>

							<div className='grid grid-cols-1 md:grid-cols-2 gap-6 mb-6'>
								<div>
									<h3 className='text-lg font-medium mb-3'>Module Usage</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='space-y-3'>
											{[
												{
													module: 'Chat',
													usage: '65%',
													color: 'bg-indigo-500',
												},
												{ module: 'RAG', usage: '20%', color: 'bg-green-500' },
												{
													module: 'Memory',
													usage: '10%',
													color: 'bg-yellow-500',
												},
												{ module: 'Agents', usage: '5%', color: 'bg-red-500' },
											].map((item, index) => (
												<div key={index}>
													<div className='flex justify-between text-sm mb-1'>
														<div>{item.module}</div>
														<div>{item.usage}</div>
													</div>
													<div className='w-full bg-gray-700 rounded-full h-2'>
														<div
															className={`h-2 rounded-full ${item.color}`}
															style={{ width: item.usage }}
														></div>
													</div>
												</div>
											))}
										</div>
									</div>
								</div>

								<div>
									<h3 className='text-lg font-medium mb-3'>
										Topic Distribution
									</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='h-48 flex items-center justify-center text-gray-500'>
											[Pie chart: Topic distribution would be displayed here]
										</div>
									</div>
								</div>
							</div>

							<div>
								<h3 className='text-lg font-medium mb-3'>
									Performance Metrics
								</h3>
								<div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='text-sm text-gray-400 mb-1'>
											Avg. Response Time
										</div>
										<div className='text-2xl font-bold'>1.2s</div>
									</div>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='text-sm text-gray-400 mb-1'>
											User Satisfaction
										</div>
										<div className='text-2xl font-bold'>94%</div>
									</div>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='text-sm text-gray-400 mb-1'>
											Daily Active Users
										</div>
										<div className='text-2xl font-bold'>24</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'composite':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h2 className='text-xl font-bold'>Dashboard Overview</h2>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='grid grid-cols-1 md:grid-cols-2 gap-6 mb-6'>
								<div>
									<h3 className='text-lg font-medium mb-3'>Recent Activity</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='space-y-3'>
											{[
												{
													activity: 'Chat about quantum computing',
													time: '2 hours ago',
													module: 'Chat',
												},
												{
													activity: 'Added new research paper',
													time: '5 hours ago',
													module: 'RAG',
												},
												{
													activity: 'Created memory entry',
													time: '1 day ago',
													module: 'Memory',
												},
												{
													activity: 'Used Research Assistant',
													time: '2 days ago',
													module: 'Agents',
												},
											].map((item, index) => (
												<div
													key={index}
													className='flex justify-between items-center pb-2 border-b border-gray-700'
												>
													<div>
														<div className='font-medium'>{item.activity}</div>
														<div className='text-xs text-gray-400'>
															{item.module}
														</div>
													</div>
													<div className='text-sm text-gray-400'>
														{item.time}
													</div>
												</div>
											))}
										</div>
									</div>
								</div>

								<div>
									<h3 className='text-lg font-medium mb-3'>System Status</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='space-y-3'>
											{[
												{
													component: 'Chat Module',
													status: 'Operational',
													color: 'bg-green-500',
												},
												{
													component: 'RAG System',
													status: 'Operational',
													color: 'bg-green-500',
												},
												{
													component: 'Memory Store',
													status: 'Operational',
													color: 'bg-green-500',
												},
												{
													component: 'Agent Framework',
													status: 'Maintenance',
													color: 'bg-yellow-500',
												},
											].map((item, index) => (
												<div
													key={index}
													className='flex justify-between items-center'
												>
													<div className='font-medium'>{item.component}</div>
													<div className='flex items-center'>
														<div
															className={`h-2 w-2 rounded-full ${item.color} mr-2`}
														></div>
														<div className='text-sm'>{item.status}</div>
													</div>
												</div>
											))}
										</div>
									</div>
								</div>
							</div>

							<div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
								<div>
									<h3 className='text-lg font-medium mb-3'>Quick Actions</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='grid grid-cols-2 gap-3'>
											{[
												{
													icon: <MessageSquare className='h-5 w-5' />,
													label: 'New Chat',
												},
												{
													icon: <FileText className='h-5 w-5' />,
													label: 'Upload Doc',
												},
												{
													icon: <Brain className='h-5 w-5' />,
													label: 'View Memory',
												},
												{
													icon: <Bot className='h-5 w-5' />,
													label: 'Run Agent',
												},
											].map((action, index) => (
												<button
													key={index}
													className='p-3 bg-gray-700 hover:bg-gray-600 rounded-md flex flex-col items-center justify-center'
												>
													<div className='text-indigo-400 mb-1'>
														{action.icon}
													</div>
													<div className='text-sm'>{action.label}</div>
												</button>
											))}
										</div>
									</div>
								</div>

								<div className='md:col-span-2'>
									<h3 className='text-lg font-medium mb-3'>Usage Snapshot</h3>
									<div className='p-4 bg-gray-800 rounded-lg'>
										<div className='h-48 flex items-center justify-center text-gray-500'>
											[Chart: Weekly usage statistics would be displayed here]
										</div>
									</div>
								</div>
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
			case 'chat':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Live Influences</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Memory Highlights
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='text-sm mb-2'>
										User prefers detailed explanations with examples
									</div>
									<div className='text-xs text-gray-400'>
										From: Preferences cluster
									</div>
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Document Citations
								</h4>
								<div className='space-y-2'>
									{mockDocuments.slice(0, 2).map(doc => (
										<div key={doc.id} className='p-3 bg-gray-800 rounded-lg'>
											<div className='text-sm font-medium mb-1'>{doc.name}</div>
											<div className='text-xs text-gray-400'>
												Relevance: 87%
											</div>
										</div>
									))}
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Model Information
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='text-sm mb-1'>GLM-4.5 Model</div>
									<div className='text-xs text-gray-400'>Temperature: 0.7</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'rag':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Document Preview</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-4'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Quantum Computing Guide
								</h4>
								<div className='text-xs text-gray-400 mb-3'>
									PDF • 2.4MB • Uploaded today
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Full Text Preview
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg max-h-60 overflow-y-auto text-sm'>
									<p className='mb-3'>
										Quantum computing is a type of computation that harnesses
										quantum mechanical phenomena to process information. Unlike
										classical computers that use bits (0 or 1), quantum
										computers use quantum bits or qubits, which can exist in
										multiple states simultaneously.
									</p>
									<p className='mb-3'>
										The fundamental principles of quantum computing include
										superposition, entanglement, and quantum interference. These
										principles enable quantum computers to solve certain
										problems much faster than classical computers.
									</p>
									<p>
										Key applications of quantum computing include cryptography,
										optimization problems, quantum simulations, and machine
										learning.
									</p>
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Metadata
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-sm space-y-2'>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Author:</div>
										<div>Dr. Jane Smith</div>
									</div>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Pages:</div>
										<div>42</div>
									</div>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Published:</div>
										<div>2023</div>
									</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Matching Chunks
								</h4>
								<div className='space-y-2'>
									{[
										{
											content:
												'Quantum bits or qubits can exist in multiple states simultaneously',
											relevance: '95%',
										},
										{
											content:
												'Key applications include cryptography and optimization problems',
											relevance: '87%',
										},
										{
											content:
												'Quantum computers use quantum mechanical phenomena to process information',
											relevance: '92%',
										},
									].map((chunk, index) => (
										<div key={index} className='p-3 bg-gray-800 rounded-lg'>
											<div className='text-sm mb-1'>{chunk.content}</div>
											<div className='text-xs text-gray-400'>
												Relevance: {chunk.relevance}
											</div>
										</div>
									))}
								</div>
							</div>
						</div>
					</div>
				);
			case 'memory':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Memory Details</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-4'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Quantum Basics
								</h4>
								<div className='text-xs text-gray-400 mb-3'>
									Science cluster • Created today
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Memory Content
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-sm'>
									Fundamental principles of quantum computing including
									superposition, entanglement, and quantum interference. These
									principles enable quantum computers to solve certain problems
									much faster than classical computers.
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Memory Extraction Summary
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='text-sm mb-3'>
										This memory was extracted from conversation about quantum
										computing on 2023-11-15.
									</div>
									<div className='text-xs text-gray-400'>Confidence: 94%</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Related Memories
								</h4>
								<div className='space-y-2'>
									{mockMemoryEntries
										.filter(m => m.id !== '1')
										.map(memory => (
											<div
												key={memory.id}
												className='p-3 bg-gray-800 rounded-lg'
											>
												<div className='text-sm font-medium mb-1'>
													{memory.title}
												</div>
												<div className='text-xs text-gray-400'>
													{memory.cluster} cluster
												</div>
											</div>
										))}
								</div>
							</div>
						</div>
					</div>
				);
			case 'agent':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Agent Configuration</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Research Assistant
								</h4>
								<div className='text-xs text-gray-400 mb-3'>Status: Active</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Parameters
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg space-y-3'>
									<div>
										<div className='text-sm text-gray-400 mb-1'>
											Search Depth
										</div>
										<select className='w-full p-2 bg-gray-700 rounded-md text-sm'>
											<option>Basic</option>
											<option selected>Standard</option>
											<option>Deep</option>
										</select>
									</div>
									<div>
										<div className='text-sm text-gray-400 mb-1'>
											Result Count
										</div>
										<select className='w-full p-2 bg-gray-700 rounded-md text-sm'>
											<option>5 results</option>
											<option selected>10 results</option>
											<option>20 results</option>
										</select>
									</div>
									<div>
										<div className='text-sm text-gray-400 mb-1'>
											Citation Style
										</div>
										<select className='w-full p-2 bg-gray-700 rounded-md text-sm'>
											<option>APA</option>
											<option selected>MLA</option>
											<option>Chicago</option>
										</select>
									</div>
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Trace Information
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-sm space-y-2'>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Last Run:</div>
										<div>Today, 10:30 AM</div>
									</div>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Execution Time:</div>
										<div>4.2 seconds</div>
									</div>
									<div className='flex justify-between'>
										<div className='text-gray-400'>Status:</div>
										<div className='text-green-400'>Completed</div>
									</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Configuration YAML
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-xs font-mono overflow-x-auto'>
									<pre>{`agent:
  name: Research Assistant
  version: 1.2.0
  parameters:
    search_depth: standard
    result_count: 10
    citation_style: MLA`}</pre>
								</div>
							</div>
						</div>
					</div>
				);
			case 'inspector':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Source Expansion</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Retrieved Document
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='text-sm font-medium mb-1'>
										Quantum Computing Guide
									</div>
									<div className='text-xs text-gray-400 mb-3'>
										Page 12 of 42
									</div>
									<div className='text-sm'>
										<p className='mb-3'>
											Quantum bits or qubits can exist in multiple states
											simultaneously due to the principle of superposition. This
											property allows quantum computers to process a vast number
											of possibilities at once.
										</p>
										<p>
											When qubits become entangled, the state of one qubit is
											dependent on the state of another, regardless of the
											distance between them. This phenomenon enables quantum
											computers to perform complex calculations much faster than
											classical computers.
										</p>
									</div>
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Token View
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-sm font-mono overflow-x-auto'>
									<div className='flex flex-wrap'>
										{[
											'Quantum',
											'bits',
											'or',
											'qubits',
											'can',
											'exist',
											'in',
											'multiple',
											'states',
											'simultaneously',
											'due',
											'to',
											'the',
											'principle',
											'of',
											'superposition',
										].map((token, index) => (
											<span
												key={index}
												className='px-2 py-1 m-1 bg-gray-700 rounded'
											>
												{token}
											</span>
										))}
									</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Trace Log
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg text-xs font-mono max-h-60 overflow-y-auto'>
									<div className='space-y-1'>
										<div>[10:30:15] Starting query analysis</div>
										<div>
											[10:30:16] Identified key entities: quantum, computing
										</div>
										<div>[10:30:17] Searching memory for relevant entries</div>
										<div>[10:30:18] Found 2 memory matches</div>
										<div>[10:30:19] Retrieving documents from RAG system</div>
										<div>[10:30:21] Retrieved 3 documents</div>
										<div>[10:30:22] Extracting relevant passages</div>
										<div>[10:30:24] Generated response with sources</div>
										<div>[10:30:25] Completed processing</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'analytics':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Statistics Details</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Module Statistics
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg space-y-3'>
									<div>
										<div className='flex justify-between text-sm mb-1'>
											<div>Chat Module</div>
											<div>65% of usage</div>
										</div>
										<div className='w-full bg-gray-700 rounded-full h-2'>
											<div
												className='h-2 rounded-full bg-indigo-500'
												style={{ width: '65%' }}
											></div>
										</div>
									</div>
									<div>
										<div className='flex justify-between text-sm mb-1'>
											<div>RAG System</div>
											<div>20% of usage</div>
										</div>
										<div className='w-full bg-gray-700 rounded-full h-2'>
											<div
												className='h-2 rounded-full bg-green-500'
												style={{ width: '20%' }}
											></div>
										</div>
									</div>
									<div>
										<div className='flex justify-between text-sm mb-1'>
											<div>Memory Store</div>
											<div>10% of usage</div>
										</div>
										<div className='w-full bg-gray-700 rounded-full h-2'>
											<div
												className='h-2 rounded-full bg-yellow-500'
												style={{ width: '10%' }}
											></div>
										</div>
									</div>
									<div>
										<div className='flex justify-between text-sm mb-1'>
											<div>Agent Framework</div>
											<div>5% of usage</div>
										</div>
										<div className='w-full bg-gray-700 rounded-full h-2'>
											<div
												className='h-2 rounded-full bg-red-500'
												style={{ width: '5%' }}
											></div>
										</div>
									</div>
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Performance Metrics
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg space-y-3'>
									<div className='flex justify-between text-sm'>
										<div>Average Response Time</div>
										<div>1.2 seconds</div>
									</div>
									<div className='flex justify-between text-sm'>
										<div>User Satisfaction</div>
										<div>94%</div>
									</div>
									<div className='flex justify-between text-sm'>
										<div>System Uptime</div>
										<div>99.8%</div>
									</div>
									<div className='flex justify-between text-sm'>
										<div>Error Rate</div>
										<div>0.2%</div>
									</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Usage Trends
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='h-48 flex items-center justify-center text-gray-500'>
										[Detailed usage trend chart would be displayed here]
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			case 'composite':
				return (
					<div className='flex flex-col h-full'>
						<div className='p-4 border-b border-gray-700'>
							<h3 className='text-lg font-medium'>Dashboard Details</h3>
						</div>
						<div className='flex-1 overflow-y-auto p-4'>
							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Recent Chat Prompts
								</h4>
								<div className='space-y-2'>
									{[
										'Explain quantum computing in simple terms',
										'What are the latest developments in AI?',
										'How do I optimize my machine learning model?',
									].map((prompt, index) => (
										<div key={index} className='p-3 bg-gray-800 rounded-lg'>
											<div className='text-sm'>{prompt}</div>
											<div className='text-xs text-gray-400 mt-1'>
												Today, {10 + index}:30 AM
											</div>
										</div>
									))}
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Most Active Memory Entries
								</h4>
								<div className='space-y-2'>
									{mockMemoryEntries.map(memory => (
										<div key={memory.id} className='p-3 bg-gray-800 rounded-lg'>
											<div className='text-sm font-medium'>{memory.title}</div>
											<div className='text-xs text-gray-400 mt-1'>
												Accessed 5 times today
											</div>
										</div>
									))}
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Last Used RAG Documents
								</h4>
								<div className='space-y-2'>
									{mockDocuments.slice(0, 2).map(doc => (
										<div key={doc.id} className='p-3 bg-gray-800 rounded-lg'>
											<div className='text-sm font-medium'>{doc.name}</div>
											<div className='text-xs text-gray-400 mt-1'>
												Used 2 hours ago
											</div>
										</div>
									))}
								</div>
							</div>

							<div className='mb-6'>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Agent Results
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='text-sm font-medium mb-1'>
										Research Assistant
									</div>
									<div className='text-xs text-gray-400 mb-2'>
										Completed: "Quantum computing research"
									</div>
									<div className='text-xs text-gray-400'>
										Duration: 4.2 seconds
									</div>
								</div>
							</div>

							<div>
								<h4 className='text-sm font-medium text-gray-400 mb-2'>
									Usage Snapshot
								</h4>
								<div className='p-3 bg-gray-800 rounded-lg'>
									<div className='grid grid-cols-2 gap-4 text-sm'>
										<div>
											<div className='text-gray-400'>Daily Active Users</div>
											<div className='text-lg font-medium'>24</div>
										</div>
										<div>
											<div className='text-gray-400'>Weekly Queries</div>
											<div className='text-lg font-medium'>142</div>
										</div>
										<div>
											<div className='text-gray-400'>Documents Processed</div>
											<div className='text-lg font-medium'>37</div>
										</div>
										<div>
											<div className='text-gray-400'>Memory Entries</div>
											<div className='text-lg font-medium'>89</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				);
			default:
				return null;
		}
	};

	return (
		<div className='flex flex-col h-screen bg-gray-900 text-gray-100'>
			{/* Top Navigation Bar */}
			<div className='flex items-center justify-between p-4 border-b border-gray-800'>
				<div className='flex items-center'>
					<div className='text-xl font-bold mr-8'>SelfRAG</div>
					<div className='flex space-x-1'>
						{[
							{
								id: 'composite',
								icon: <Home className='h-5 w-5' />,
								label: 'Overview',
							},
							{
								id: 'chat',
								icon: <MessageSquare className='h-5 w-5' />,
								label: 'Chat',
							},
							{
								id: 'rag',
								icon: <FileText className='h-5 w-5' />,
								label: 'RAG',
							},
							{
								id: 'memory',
								icon: <Brain className='h-5 w-5' />,
								label: 'Memory',
							},
							{
								id: 'agent',
								icon: <Bot className='h-5 w-5' />,
								label: 'Agents',
							},
							{
								id: 'inspector',
								icon: <Eye className='h-5 w-5' />,
								label: 'Inspector',
							},
							{
								id: 'analytics',
								icon: <BarChart3 className='h-5 w-5' />,
								label: 'Analytics',
							},
						].map(item => (
							<button
								key={item.id}
								onClick={() => setActiveModule(item.id as any)}
								className={`flex items-center px-3 py-2 rounded-md text-sm ${
									activeModule === item.id
										? 'bg-indigo-600'
										: 'hover:bg-gray-800'
								}`}
							>
								<span className='mr-2'>{item.icon}</span>
								<span>{item.label}</span>
							</button>
						))}
					</div>
				</div>
				<div className='flex items-center space-x-4'>
					<button className='p-2 rounded-full hover:bg-gray-800'>
						<Settings className='h-5 w-5' />
					</button>
					<div className='h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center'>
						<User className='h-4 w-4' />
					</div>
				</div>
			</div>

			{/* Main Content Area */}
			<div className='flex flex-1 overflow-hidden'>
				{/* Left Panel */}
				<div
					className={`${
						leftPanelCollapsed ? 'w-0' : 'w-64'
					} border-r border-gray-800 flex flex-col transition-all duration-300 overflow-hidden`}
				>
					{renderLeftPanel()}
				</div>

				{/* Center Panel */}
				<div className='flex-1 flex flex-col'>{renderCenterPanel()}</div>

				{/* Right Panel */}
				<div
					className={`${
						rightPanelCollapsed ? 'w-0' : 'w-80'
					} border-l border-gray-800 flex flex-col transition-all duration-300 overflow-hidden`}
				>
					{renderRightPanel()}
				</div>

				{/* Panel Toggle Buttons */}
				<div className='absolute left-64 top-1/2 transform -translate-y-1/2 z-10'>
					<button
						onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
						className='p-1 bg-gray-800 rounded-r-md border border-gray-700'
					>
						{leftPanelCollapsed ? (
							<ChevronRight className='h-4 w-4' />
						) : (
							<ChevronLeft className='h-4 w-4' />
						)}
					</button>
				</div>

				<div className='absolute right-80 top-1/2 transform -translate-y-1/2 z-10'>
					<button
						onClick={() => setRightPanelCollapsed(!rightPanelCollapsed)}
						className='p-1 bg-gray-800 rounded-l-md border border-gray-700'
					>
						{rightPanelCollapsed ? (
							<ChevronLeft className='h-4 w-4' />
						) : (
							<ChevronRight className='h-4 w-4' />
						)}
					</button>
				</div>
			</div>
		</div>
	);
}
