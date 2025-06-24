import React, { useState, useRef, KeyboardEvent, ChangeEvent } from 'react';
import { 
  Box, 
  Input, 
  Button, 
  Flex, 
  Icon, 
  InputGroup, 
  InputLeftElement, 
  InputRightElement,
  Text
} from '@chakra-ui/react';
import { FaPaperPlane, FaLink, FaGithub } from 'react-icons/fa';

// Create icon components with proper typing
type IconComponent = React.FC<{ className?: string }>;

const PaperPlaneIcon: IconComponent = () => <FaPaperPlane />;
const LinkIcon: IconComponent = () => <FaLink />;
const GithubIcon: IconComponent = () => <FaGithub />;

interface ChatInputProps {
  onSendMessage: (message: string, repoUrl: string) => void;
  isProcessing: boolean;
  onIndexRepository: (repoUrl: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isProcessing,
  onIndexRepository
}) => {
  const [message, setMessage] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSendMessage = () => {
    if (message.trim() && repoUrl.trim()) {
      onSendMessage(message, repoUrl);
      setMessage('');
      
      // Focus the input after sending
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleIndexClick = () => {
    if (repoUrl.trim()) {
      onIndexRepository(repoUrl);
    }
  };

  const isFormValid = message.trim().length > 0 && repoUrl.trim().length > 0;
  const isRepoUrlValid = repoUrl.trim().length > 0;

  return (
    <Box w="100%" mb={4} px={4} maxW="800px" mx="auto">
      <Flex direction="column" gap={4}>
        <Box>
          <Text fontSize="sm" mb={2} color="gray.600">
            GitHub Repository URL
          </Text>
          <InputGroup size="md">
            <InputLeftElement pointerEvents="none">
              <Icon as={GithubIcon} color="gray.500" />
            </InputLeftElement>
            <Input
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setRepoUrl(e.target.value)}
              isDisabled={isProcessing}
              variant="filled"
              pr="5.5rem"
              pl={10}
              onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.focus()}
            />
            <InputRightElement width="6rem">
              <Button
                size="sm"
                h="1.75rem"
                colorScheme="blue"
                onClick={handleIndexClick}
                isLoading={isProcessing}
                loadingText="Indexing"
                isDisabled={!isRepoUrlValid}
                mr={1}
              >
                Index
              </Button>
            </InputRightElement>
          </InputGroup>
        </Box>

        <Box>
          <Text fontSize="sm" mb={2} color="gray.600">
            Your Question
          </Text>
          <InputGroup size="md">
            <Input
              ref={inputRef}
              placeholder="Ask anything about the repository..."
              value={message}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              isDisabled={isProcessing || !isRepoUrlValid}
              variant="filled"
              pr="5.5rem"
            />
            <InputRightElement width="5.5rem">
              <Button
                size="sm"
                h="1.75rem"
                colorScheme="blue"
                onClick={handleSendMessage}
                isLoading={isProcessing}
                loadingText="Sending"
                isDisabled={!isFormValid}
                rightIcon={<Icon as={PaperPlaneIcon} />}
                mr={1}
              >
                Send
              </Button>
            </InputRightElement>
          </InputGroup>
        </Box>
      </Flex>
    </Box>
  );
};
