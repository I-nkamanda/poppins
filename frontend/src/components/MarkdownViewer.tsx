import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewerProps {
    content: string;
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
    return (
        <div className="prose prose-lg prose-indigo max-w-none prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-p:text-gray-700 break-words">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // 코드 블록 처리
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        const language = match ? match[1] : '';

                        if (inline) {
                            return (
                                <code className="px-1.5 py-0.5 rounded bg-gray-100 text-pink-600 text-sm font-mono font-medium" {...props}>
                                    {children}
                                </code>
                            );
                        }

                        return (
                            <div className="relative my-6 group">
                                {language && (
                                    <div className="absolute top-0 right-0 px-3 py-1 text-xs font-sans font-medium text-gray-400 bg-gray-800 rounded-bl-lg rounded-tr-lg border-b border-l border-gray-700 z-10">
                                        {language}
                                    </div>
                                )}
                                <pre className="!bg-[#1e1e1e] !text-[#d4d4d4] !p-5 !rounded-lg overflow-x-auto border border-gray-800 shadow-md !m-0">
                                    <code className={`text-sm font-mono leading-relaxed ${className || ''}`} {...props}>
                                        {children}
                                    </code>
                                </pre>
                            </div>
                        );
                    },
                    // 문단 처리 - word-break 추가
                    p({ children, ...props }: any) {
                        return (
                            <p className="break-words whitespace-pre-wrap mb-4" {...props}>
                                {children}
                            </p>
                        );
                    },
                    // 헤더 크기 조정 (너무 크지 않게)
                    h1({ children, ...props }: any) {
                        return <h1 className="text-2xl font-bold mt-8 mb-4 text-gray-900" {...props}>{children}</h1>;
                    },
                    h2({ children, ...props }: any) {
                        return <h2 className="text-xl font-bold mt-6 mb-3 text-gray-900" {...props}>{children}</h2>;
                    },
                    h3({ children, ...props }: any) {
                        return <h3 className="text-lg font-bold mt-4 mb-2 text-gray-900" {...props}>{children}</h3>;
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
