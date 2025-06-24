import React from 'react';
import { Box, Text, Icon, BoxProps, Code, useColorModeValue } from '@chakra-ui/react';
import { FaGithub, FaUser } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

interface CodeChunkProps extends BoxProps {
  children: React.ReactNode;
}

interface CodeChunkProps extends BoxProps {
  children: React.ReactNode;
}

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  // Define colors based on color mode
  const userBgColor = useColorModeValue('blue.50', 'blue.900');
  const botBgColor = useColorModeValue('gray.50', 'gray.700');
  const chunkBgColor = useColorModeValue('whiteAlpha.700', 'whiteAlpha.100');
  
  // Set component props based on message sender
  const isUser = message.sender === 'user';
  const bgColor = isUser ? userBgColor : botBgColor;
  const align = isUser ? 'flex-end' : 'flex-start';
  const iconColor = isUser ? 'blue.500' : 'gray.500';
  const icon = isUser ? FaUser : FaGithub;

  return (
    <Box
      alignSelf={align}
      bg={bgColor}
      borderRadius="lg"
      p={4}
      maxW="80%"
      w="fit-content"
      boxShadow="sm"
      mb={4}
    >
      <Box display="flex" gap="0.75rem" alignItems="flex-start">
        <Icon as={icon as React.ElementType} color={iconColor} boxSize="1.25rem" mt="0.25rem" />
        <Box
          display="flex"
          flexDirection="column"
          gap="0.5rem"
          w="100%"
        >
          <Box fontSize="sm" color="gray.500">
            {message.sender === 'user' ? 'You' : 'GitHub Assistant'}
          </Box>
          <Box>
            <ReactMarkdown
              components={{
                code({node, className, children, ...props}) {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !className?.includes('language-');
                  return isInline ? (
                    <Code
                      className={className}
                      p={2}
                      w="100%"
                      borderRadius="md"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </Code>
                  ) : (
                    <Code className={className} {...props}>
                      {children}
                    </Code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </Box>
          {message.chunks && message.chunks.length > 0 && (
            <Box display="flex" flexDirection="column" gap="0.5rem" w="100%" mt={2}>
              <Text fontSize="xs" color="gray.500">Relevant code:</Text>
              {message.chunks?.map((chunk, index) => (
                <Box
                  key={index}
                  bg={chunkBgColor}
                  p={2}
                  borderRadius="md"
                  fontSize="xs"
                  fontFamily="mono"
                  whiteSpace="pre-wrap"
                  overflowX="auto"
                >
                  <Text fontSize="xs" color="blue.400" mb={1}>
                    {chunk.file_path}
                  </Text>
                  <Text fontSize="xs">{chunk.text}</Text>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};
