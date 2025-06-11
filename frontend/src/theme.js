// src/theme.js
import { extendTheme } from "@chakra-ui/react";  // now works!

const config = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

const theme = extendTheme({ config });

export default theme;
