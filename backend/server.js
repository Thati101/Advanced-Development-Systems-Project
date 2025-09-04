const express = require("express");
const http = require("http");
const { Server } = require("socket.io");

const app = express();
app.use(express.json());
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: "*" }
});

// Mock DB (replace with real DB later)
let chats = [
  // { id: 1, users: [1, 3], product: 101, messages: [...] }
];
let nextChatId = 1;

// Get all chats for a user
app.get("/api/chats", (req, res) => {
  const userId = parseInt(req.query.userId);
  const userChats = chats.filter(chat => chat.users.includes(userId));
  res.json(userChats);
});

// Get or create chat for two users and a product
app.post("/api/chats/find_or_create", (req, res) => {
  const { user1, user2, product } = req.body;
  let chat = chats.find(
    c =>
      c.product === product &&
      c.users.includes(user1) &&
      c.users.includes(user2)
  );
  if (!chat) {
    chat = {
      id: nextChatId++,
      users: [user1, user2],
      product,
      messages: []
    };
    chats.push(chat);
  }
  res.json(chat);
});

// Get messages for a chat
app.get("/api/chats/:chatId/messages", (req, res) => {
  const chatId = parseInt(req.params.chatId);
  const chat = chats.find(c => c.id === chatId);
  res.json(chat ? chat.messages : []);
});

// Add message to chat
app.post("/api/chats/:chatId/messages", (req, res) => {
  const chatId = parseInt(req.params.chatId);
  const { sender, text } = req.body;
  const chat = chats.find(c => c.id === chatId);
  if (chat) {
    const message = { sender, text, timestamp: Date.now() };
    chat.messages.push(message);
    io.to(`chat_${chatId}`).emit("receive_message", message);
    res.json(message);
  } else {
    res.status(404).json({ error: "Chat not found" });
  }
});

// --- Socket.IO events ---
io.on("connection", (socket) => {
  console.log("User connected:", socket.id);

  // Join chat room
  socket.on("join_chat", (chatId) => {
    socket.join(`chat_${chatId}`);
    console.log(`Socket ${socket.id} joined chat_${chatId}`);
  });

  // Send message to chat room
  socket.on("send_message", (data) => {
    // data: { chatId, sender, text }
    io.to(`chat_${data.chatId}`).emit("receive_message", {
      sender: data.sender,
      text: data.text,
      timestamp: Date.now()
    });
  });

  socket.on("disconnect", () => {
    console.log("User disconnected:", socket.id);
  });
});

server.listen(5000, () => {
  console.log("Socket.IO + API server running on http://localhost:5000");
});
