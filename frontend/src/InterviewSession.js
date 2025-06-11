import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Flex,
  Text,
  Input,
  IconButton,
  Spinner,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react";
import { FaPaperPlane } from "react-icons/fa";
import { nextQuestion, getFeedback } from "./api";

export default function InterviewSession({ sessionId, firstQuestion }) {
  const [history, setHistory] = useState([
    { role: "ai", content: firstQuestion },
  ]);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const bottomRef = useRef(null);
  const toast = useToast();

  // Auto-scroll to bottom when history or feedback changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, feedback]);

  // Colors & styles
  const containerBg = useColorModeValue("rgba(255,255,255,0.1)", "rgba(0,0,0,0.4)");
  const aiBubbleBg = useColorModeValue("whiteAlpha.300", "whiteAlpha.200");
  const userBubbleBg = useColorModeValue("purple.600", "purple.500");
  const inputBg = useColorModeValue("whiteAlpha.200", "whiteAlpha.100");
  const textColor = useColorModeValue("gray.900", "gray.50");

  const handleSubmit = async () => {
    if (!answer.trim()) return;
    setLoading(true);

    try {
      // Add user message to history
      setHistory((h) => [...h, { role: "user", content: answer }]);

      // Fetch AI follow-up
      const response = await nextQuestion(sessionId, answer);
      setHistory((h) => [...h, { role: "ai", content: response.question }]);

      // If interview ends, get feedback
      if (response.feedback || /thank you/i.test(response.question)) {
        const { feedback } = response.feedback ? response : await getFeedback(sessionId);
        setFeedback(feedback);
      }

      setAnswer("");
    } catch (err) {
      toast({
        title: "Error",
        description: err.message || "Failed to fetch response from server",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      console.error("Submit error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex
      direction="column"
      h="80vh"
      w="full"
      maxW="600px"
      mx="auto"
      mt="8"
      p="4"
      bg={containerBg}
      backdropFilter="blur(12px)"
      borderRadius="xl"
      boxShadow="xl"
    >
      {/* Chat window */}
      <Box flex="1" overflowY="auto" mb="4">
        {history.map((turn, i) => (
          <Flex
            key={i}
            justify={turn.role === "ai" ? "flex-start" : "flex-end"}
            mb="2"
          >
            <Box
              bg={turn.role === "ai" ? aiBubbleBg : userBubbleBg}
              color={textColor}
              px="4"
              py="2"
              borderRadius="lg"
              maxW="80%"
              whiteSpace="pre-wrap"
              wordBreak="break-word"
            >
              {turn.content}
            </Box>
          </Flex>
        ))}

        {/* Typing indicator */}
        {loading && (
          <Flex mb="2" align="center">
            <Spinner size="sm" color={textColor} mr="2" />
            <Text color={textColor} fontSize="sm" fontStyle="italic">
              AI is typing…
            </Text>
          </Flex>
        )}

        <div ref={bottomRef} />
      </Box>

      {/* Feedback view */}
      {feedback ? (
        <Box maxH="40vh" overflowY="auto" p="2">
          <Text color={textColor} whiteSpace="pre-wrap">
            {feedback}
          </Text>
        </Box>
      ) : (
        /* Input bar */
        <Flex>
          <Input
            bg={inputBg}
            color={textColor}
            placeholder="Type your answer..."
            _placeholder={{ color: "gray.400" }}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          <IconButton
            ml="2"
            colorScheme="purple"
            icon={<FaPaperPlane />}
            onClick={handleSubmit}
            isLoading={loading}
            aria-label="Send answer"
          />
        </Flex>
      )}
    </Flex>
  );
}