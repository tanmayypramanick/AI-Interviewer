import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Flex,
  Center,
  Heading,
  Text,
  Input,
  Button,
  Textarea,
  Icon,
  HStack,
  IconButton
} from "@chakra-ui/react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { FaFilePdf, FaPaperPlane, FaComments, FaMicrophone, FaLightbulb, FaBrain } from "react-icons/fa";
import { keyframes } from "@emotion/react";

import { startInterview } from "./api";
import InterviewSession from "./InterviewSession";
import LoadingScreen from "./LoadingScreen";

const MotionBox = motion(Box);

// Background pulse
const bgPulse = keyframes`
  0%, 100% { background-position: 50% 50%; }
  50% { background-position: 52% 48%; }
`;

// Slide + fade animation
const slideFade = {
  hidden: { y: -30, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};

export default function App() {
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDesc, setJobDesc] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [firstQuestion, setFirstQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef();

  useEffect(() => {
    inputRef.current?.focus();
  }, [step]);

  const onDrop = (files) => {
    const pdf = files.find((f) => f.type === "application/pdf");
    if (pdf) {
      console.log("Selected resume:", pdf.name);
      setResumeFile(pdf);
    }
  };
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [] },
    multiple: false,
  });

  const features = [
    { icon: FaComments, text: "Context-Aware Q&A" },
    { icon: FaBrain, text: "Multi-Turn Conversation Memory" },
    { icon: FaLightbulb, text: "Role-Specific Interview" },
  ];

  const launchInterview = async () => {
    if (!name.trim() || !resumeFile) {
      alert("Please provide a name and resume.");
      return;
    }
    
    try {
      setIsLoading(true);
      console.log("Starting interview with:", { name, resume: resumeFile.name, jobDesc });
      const { session_id, question } = await startInterview(
        name,
        resumeFile,
        jobDesc.trim() || null // Send null if jobDesc is empty
      );
      console.log("Interview started:", { session_id, question });
      setSessionId(session_id);
      setFirstQuestion(question);
      setIsLoading(false);
      setStep(4);
    } catch (err) {
      console.error("Failed to start interview:", err);
      alert(`Error starting interview: ${err.message}`);
      setIsLoading(false);
    }
  };

  return (
    <Box pos="relative" h="100vh" w="100vw" overflow="hidden">
      {/* Background */}
      <Box
        pos="absolute" top={0} left={0}
        w="100%" h="100%"
        bg="radial-gradient(circle at center, rgb(51, 5, 79), rgb(8, 2, 12), #000)"
        bgSize="200% 200%"
        animation={`${bgPulse} 30s ease infinite`}
        zIndex={-1}
      />

      {/* Floating Dots */}
      {[...Array(50)].map((_, i) => (
        <MotionBox
          key={i}
          pos="absolute" w="3px" h="3px" bg="whiteAlpha.600" rounded="full"
          style={{ top: `${Math.random() * 100}%`, left: `${Math.random() * 100}%` }}
          animate={{ y: [0, -8, 0] }}
          transition={{
            repeat: Infinity,
            duration: 4 + Math.random() * 4,
            delay: Math.random() * 4,
          }}
        />
      ))}

      {/* Logo */}
      <Flex pos="fixed" top={4} left={6} zIndex={2}>
        <Heading size="lg" fontWeight="black">
          <Text as="span" color="purple.300">Crack</Text>
          <Text as="span" color="pink.300">it</Text>
        </Heading>
      </Flex>

      {/* Main Content */}
      <Center h="100%" flexDir="column" textAlign="center" px={4} color="white" zIndex={1}>
        {/* Show loading screen if waiting */}
        {isLoading ? (
          <LoadingScreen />
        ) : (
          <AnimatePresence exitBeforeEnter>
            {/* Step 0: Hero */}
            {step === 0 && (
              <MotionBox
                key="hero"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={slideFade}
                transition={{ duration: 0.8 }}
                maxW="700px"
              >
                <Heading
                  fontSize={{ base: "3xl", md: "5xl" }}
                  bgGradient="linear(to-r, purple.300, pink.400)"
                  bgClip="text"
                  mb={2}
                >
                  Master Your Interview
                </Heading>
                <Heading
                  fontSize={{ base: "2xl", md: "3xl" }}
                  bgGradient="linear(to-r, purple.400, pink.600)"
                  bgClip="text"
                  mb={4}
                >
                  Crack It with AI Practice
                </Heading>
                <Text fontSize={{ base: "md", md: "lg" }} mb={6} color="whiteAlpha.800">
                  Experience real-time mock interviews with smart voice & video cues, tailored feedback, and seamless prep.
                </Text>
                <HStack spacing={4} justify="center" mb={8}>
                  <Button size="lg" colorScheme="purple" onClick={() => setStep(1)}>
                    Get Started
                  </Button>
                  <Button size="lg" variant="outline" borderColor="purple.500" onClick={() => setStep(1)}>
                    Learn More
                  </Button>
                </HStack>
                <HStack spacing={12} justify="center">
                  {features.map(({ icon, text }, idx) => (
                    <MotionBox
                      key={idx}
                      initial="hidden"
                      animate="visible"
                      variants={slideFade}
                      transition={{ duration: 0.6, delay: 0.3 + idx * 0.2 }}
                    >
                      <HStack spacing={2}>
                        <Icon as={icon} boxSize={5} color="purple.300" />
                        <Text>{text}</Text>
                      </HStack>
                    </MotionBox>
                  ))}
                </HStack>
              </MotionBox>
            )}

            {/* Step 1: Name Input */}
            {step === 1 && (
              <MotionBox
                key="name"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={slideFade}
                transition={{ duration: 0.6 }}
              >
                <Heading
                  fontSize="2xl"
                  bgGradient="linear(to-r, purple.300, pink.400)"
                  bgClip="text"
                  mb={4}
                >
                  What should we call you?
                </Heading>

                {/* Input and button together */}
                <Flex maxW="350px" mx="auto" align="center">
                  <Input
                    ref={inputRef}
                    placeholder="Enter your name..."
                    borderRadius="full"
                    bg="whiteAlpha.200"
                    _placeholder={{ color: "whiteAlpha.500" }}
                    color="purple.200"
                    textAlign="center"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.target.value.trim()) {
                        setStep(2);
                      }
                    }}
                  />
                  <IconButton
                    ml="2"
                    icon={<FaPaperPlane />}
                    colorScheme="purple"
                    aria-label="Submit name"
                    borderRadius="full"
                    onClick={() => {
                      if (name.trim()) {
                        setStep(2);
                      }
                    }}
                  />
                </Flex>
              </MotionBox>
            )}

            {/* Step 2: Resume Upload */}
            {step === 2 && (
              <MotionBox
                key="resume"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={slideFade}
                transition={{ duration: 0.6 }}
                textAlign="center"
              >
                <Heading
                  fontSize="2xl"
                  bgGradient="linear(to-r, purple.300, pink.400)"
                  bgClip="text"
                  mb={2}
                >
                  👋 Hi {name}!
                </Heading>
                <Text fontSize="lg" color="whiteAlpha.800" mb={4}>
                  Please upload your resume to get to know you better.
                </Text>
                <Box
                  {...getRootProps()}
                  p={8}
                  maxW="350px"
                  mx="auto"
                  border="2px dashed"
                  borderColor="purple.500"
                  borderRadius="md"
                  bg="whiteAlpha.100"
                  cursor="pointer"
                >
                  <input {...getInputProps()} />
                  <Text mb={2}>
                    {resumeFile
                      ? resumeFile.name
                      : isDragActive
                        ? "Drop it here…"
                        : "Drag & drop or click to upload"}
                  </Text>
                  <HStack justify="center" spacing={2} mt={2}>
                    <Icon as={FaFilePdf} boxSize={4} color="purple.300" />
                    <Text fontSize="sm" color="purple.300" fontStyle="italic">
                      PDF format only
                    </Text>
                  </HStack>
                </Box>
                {resumeFile && (
                  <Button mt={6} colorScheme="purple" onClick={() => setStep(3)}>
                    Next
                  </Button>
                )}
              </MotionBox>
            )}

            {/* Step 3: Job Description Paste */}
            {step === 3 && (
              <MotionBox
                key="job-desc"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={slideFade}
                transition={{ duration: 0.6 }}
                maxW="500px"
              >
                <Heading
                  fontSize="2xl"
                  bgGradient="linear(to-r, purple.200, pink.400)"
                  bgClip="text"
                  mb={3}
                >
                  Lastly, paste your job description
                </Heading>
                <Text fontSize="md" mb={4} color="whiteAlpha.700">
                  If you'd like a role-specific mock interview (optional):
                </Text>
                <Textarea
                  ref={inputRef}
                  placeholder="Paste job description..."
                  value={jobDesc}
                  onChange={(e) => setJobDesc(e.target.value)}
                  bg="whiteAlpha.200"
                  borderRadius="md"
                  _placeholder={{ color: "whiteAlpha.500" }}
                  h="150px"
                />
                <HStack spacing={4} mt={6} justify="center">
                  <Button colorScheme="purple" onClick={launchInterview}>
                    Take Mock Interview
                  </Button>
                  <Button
                    variant="outline"
                    borderColor="purple.400"
                    onClick={launchInterview}
                  >
                    Questions You Should Prepare
                  </Button>
                </HStack>
              </MotionBox>
            )}

            {/* Step 4: Live Interview Chat */}
            {step === 4 && sessionId && (
              <InterviewSession sessionId={sessionId} firstQuestion={firstQuestion} />
            )}
          </AnimatePresence>
        )}
      </Center>
    </Box>
  );
}