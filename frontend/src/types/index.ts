export interface Chunk {
  text: string;
  file_path: string;
}

export interface QueryResponse {
  answer: string;
  chunks: Chunk[];
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  chunks?: Chunk[];
}

export interface IndexRequest {
  repo_url: string;
  branch?: string;
}

export interface QueryRequest {
  question: string;
  repo_url: string;
  top_k?: number;
}
