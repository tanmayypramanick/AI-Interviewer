// src/InterviewSessionVoice.js
import React, { useState, useEffect, useRef } from "react";
import { Box, Center, Button, Text } from "@chakra-ui/react";
import { startListening, stopListening, speakText } from "./speech";
import { nextQuestion, getFeedback } from "./api";
import { motion } from "framer-motion";

const MotionBox = motion(Box);

export default function InterviewSessionVoice({ sessionId, firstQuestion }) {
  const [aiSpeaking, setAiSpeaking] = useState(false);
  const [userSpeaking, setUserSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [listening, setListening] = useState(false);
  const [started, setStarted] = useState(false);

  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  async function handleAIResponse(text) {
    setAiSpeaking(true);

    // Adding slight human filler randomness
    const fillers = ["uhh", "let's see", "you know"];
    const shouldAddFiller = Math.random() < 0.5; // 50% chance
    if (shouldAddFiller) {
      const filler = fillers[Math.floor(Math.random() * fillers.length)];
      text = `${filler}, ${text}`;
    }

    await speakText(text);
    setAiSpeaking(false);
    listenToUser();
  }

  async function listenToUser() {
    setListening(true);
    startListening((liveText) => setTranscript(liveText));
  }

  async function handleUserSubmit() {
    stopListening();
    setListening(false);

    const finalText = transcript.trim();
    if (!finalText) return;

    const { question, end } = await nextQuestion(sessionId, finalText);
    setTranscript("");

    if (end) {
      const { feedback } = await getFeedback(sessionId);
      setFeedback(feedback);
    } else {
      await handleAIResponse(question);
    }
  }

  const startConversation = async () => {
    setStarted(true);
    await handleAIResponse(firstQuestion); // 👈 Speak FIRST before listening
  };

  return (
    <Box pos="relative" h="100vh" w="100vw" overflow="hidden">
      {/* 🔥 Background Waves */}
      <MotionBox
        pos="absolute"
        top={0} left={0}
        w="100%" h="100%"
        bgGradient={
          aiSpeaking
            ? "linear(to-r, pink.500, pink.300, purple.500)"
            : listening
            ? "linear(to-r, purple.500, purple.300, pink.500)"
            : "linear(to-r, purple.800, purple.900, black)"
        }
        backgroundSize="400% 400%"
        animate={{
          backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "linear",
        }}
        filter="blur(100px)"
        zIndex={-1}
      />

      <Center h="full" flexDir="column" color="white" textAlign="center" px={4}>
        {!started ? (
          <>
            <Text fontSize="xl" mb={4}>✅ Successfully fetched resume & job description</Text>
            <Button
              onClick={startConversation}
              size="lg"
              px={10}
              py={6}
              fontSize="2xl"
              borderRadius="full"
              bgGradient="linear(to-r, purple.400, pink.400)"
              _hover={{ bgGradient: "linear(to-r, pink.400, purple.400)" }}
            >
              🎤 Start Interview
            </Button>
          </>
        ) : feedback ? (
          <>
            <Text fontSize="2xl" mb={6}>🎉 Interview Complete!</Text>
            <Text whiteSpace="pre-wrap" maxW="600px">{feedback}</Text>
          </>
        ) : (
          <>
            {/* Listening / Speaking State */}
            <Text fontSize="3xl" mb={6} fontWeight="bold">
              {aiSpeaking ? "👩‍💻 AI is Speaking..." : listening ? "🎤 Listening to you..." : ""}
            </Text>

            {/* Show Submit button only if listening */}
            {listening && (
              <Button
                onClick={handleUserSubmit}
                size="md"
                colorScheme="pink"
                mt={4}
              >
                Submit Response
              </Button>
            )}
          </>
        )}
        <div ref={bottomRef}></div>
      </Center>
    </Box>
  );
}
