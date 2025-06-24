import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Center,
  Flex,
  Heading,
  Text,
  useColorMode,
  useColorModeValue,
  IconButton,
  useToast,
  Icon
} from '@chakra-ui/react';
import { FaGithub, FaRobot, FaMoon, FaSun } from 'react-icons/fa';

// Import components
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { api } from './services/api';
import { Message } from './types';

// Create icon components with proper typing
const GithubIcon: React.FC = () => <FaGithub />;
const RobotIcon: React.FC = () => <FaRobot />;

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const { colorMode, toggleColorMode } = useColorMode();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    setMessages((prev) => [...prev, newMessage]);
  }, []);

  const handleSendMessage = useCallback(async (content: string, repoUrl: string) => {
    const userMessage = { content, sender: 'user' as const };
    addMessage(userMessage);
    setIsProcessing(true);

    try {
      const response = await api.queryRepository({
        question: content,
        repo_url: repoUrl,
        top_k: 3
      });
      
      const botMessage = {
        content: response.answer,
        sender: 'bot' as const,
        chunks: response.chunks
      };
      addMessage(botMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        content: 'Sorry, I encountered an error processing your request.',
        sender: 'bot' as const
      };
      addMessage(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleIndexRepository = useCallback(async (repoUrl: string) => {
    if (!repoUrl) return;
    
    setIsProcessing(true);
    try {
      await api.indexRepository({ repo_url: repoUrl });
      const successMessage = {
        content: `Successfully indexed repository: ${repoUrl}`,
        sender: 'bot' as const
      };
      addMessage(successMessage);
    } catch (error) {
      console.error('Error indexing repository:', error);
      const errorMessage = {
        content: 'Failed to index repository. Please check the URL and try again.',
        sender: 'bot' as const
      };
      addMessage(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  return (
    <Flex direction="column" h="100vh" bg={bgColor}>
      {/* Header */}
      <Box
        as="header"
        borderBottomWidth="1px"
        borderColor={borderColor}
        p={4}
        bg={colorMode === 'light' ? 'white' : 'gray.800'}
        boxShadow="sm"
        position="relative"
      >
        <IconButton
          aria-label="Toggle color mode"
          icon={colorMode === 'light' ? <FaMoon /> : <FaSun />}
          onClick={toggleColorMode}
          position="absolute"
          right={4}
          top={4}
          size="sm"
          variant="ghost"
        />
        <Flex align="center" gap="0.75rem">
          <Box as="span" display="inline-flex" alignItems="center" fontSize="2rem" color="gray.600">
            <GithubIcon />
          </Box>
          <Flex direction="column" gap={0} align="flex-start">
            <Heading size="md" m={0}>Ask My GitHub</Heading>
            <Text fontSize="sm" color="gray.500" m={0}>
              Ask questions about any GitHub repository
            </Text>
          </Flex>
        </Flex>
      </Box>

      {/* Chat Area */}
      <Box flex="1" p={4} overflowY="auto">
        {messages.length === 0 ? (
          <Center h="100%" flexDirection="column" color="gray.500">
            <Box as="span" display="inline-flex" alignItems="center" fontSize="3rem" mb={4}>
              <RobotIcon />
            </Box>
            <Text fontSize="xl" fontWeight="medium" mb={2}>
              Welcome to Ask My GitHub
            </Text>
            <Text textAlign="center" maxW="md">
              Enter a GitHub repository URL and start asking questions about the codebase.
            </Text>
          </Center>
        ) : (
          <Box>
            {messages.map((message) => (
              <Box key={message.id} mb={4}>
                <ChatMessage message={message} />
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </Box>
        )}
      </Box>

      {/* Input Area */}
      <Box
        borderTopWidth="1px"
        borderColor={borderColor}
        p={4}
        bg={colorMode === 'light' ? 'white' : 'gray.800'}
      >
        <ChatInput
          onSendMessage={handleSendMessage}
          isProcessing={isProcessing}
          onIndexRepository={handleIndexRepository}
        />
      </Box>
    </Flex>
  );
};

export default App;
