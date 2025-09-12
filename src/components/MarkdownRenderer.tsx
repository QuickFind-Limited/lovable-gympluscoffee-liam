import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = "" }) => {
  return (
    <div className={`prose prose-sm max-w-none dark:prose-invert ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Personnaliser les composants pour s'adapter au design
          table: ({ children }) => (
            <div className="my-2 w-full overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/60">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-border">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-muted/40 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children, ...props }) => (
            <th
              style={(props as any).style}
              className="text-left font-semibold text-foreground px-3 py-2 border-b border-border align-middle whitespace-nowrap"
            >
              {children}
            </th>
          ),
          td: ({ children, ...props }) => (
            <td
              style={(props as any).style}
              className="text-foreground px-3 py-2 align-top border-b border-border"
            >
              {children}
            </td>
          ),
          p: ({ children }) => (
            <p className="mb-2 last:mb-0 text-sm">{children}</p>
          ),
          h1: ({ children }) => (
            <h1 className="text-lg font-bold mb-2 text-foreground">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-bold mb-2 text-foreground">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-sm font-bold mb-1 text-foreground">
              {children}
            </h3>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-4 mb-2 text-sm">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-4 mb-2 text-sm">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="mb-1 text-sm">{children}</li>
          ),
          code: ({ children, ...props }) =>
            (props as any).inline ? (
              <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono text-foreground">
                {children}
              </code>
            ) : (
              <code className="block bg-muted p-2 rounded text-xs font-mono overflow-x-auto text-foreground">
                {children}
              </code>
            ),
          pre: ({ children }) => (
            <pre className="bg-muted p-2 rounded overflow-x-auto mb-2">
              {children}
            </pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary pl-4 italic mb-2 text-muted-foreground">
              {children}
            </blockquote>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-foreground">{children}</em>
          ),
          a: ({ children, href }) => (
            <a 
              href={href} 
              className="text-primary underline hover:text-primary/80"
              target="_blank" 
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
