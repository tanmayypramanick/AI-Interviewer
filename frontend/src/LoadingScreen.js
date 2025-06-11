// src/LoadingScreen.js
import { Center, VStack, Spinner, Text } from "@chakra-ui/react";
import { keyframes } from "@emotion/react"; // 👈 Correct import for keyframes

import { motion } from "framer-motion";

const spinText = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const MotionSpinner = motion(Spinner);

export default function LoadingScreen() {
  return (
    <Center h="100vh" w="100vw" flexDirection="column" bg="transparent" color="white">
      <MotionSpinner
        size="xl"
        color="purple.400"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        mb="6"
      />
      <VStack spacing={3}>
        <Text fontSize="2xl" fontWeight="bold">
          Fetching your resume and job description...
        </Text>
        <Text fontSize="md" color="whiteAlpha.700">
          Hold tight, we’re reading everything carefully!
        </Text>
      </VStack>
    </Center>
  );
}
