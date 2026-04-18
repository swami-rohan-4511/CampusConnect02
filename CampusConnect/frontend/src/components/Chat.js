import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  Send,
  Close,
  Chat as ChatIcon,
  Person,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';

const Chat = ({ recipientId, chatId, itemId = null }) => {
  const theme = useTheme();
  const { user, token } = useSelector((state) => state.auth);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const websocketRef = useRef(null);
  const messagesEndRef = useRef(null);

  const WEBSOCKET_URL = process.env.REACT_APP_WEBSOCKET_URL || '';

  useEffect(() => {
    if (open && user && token) {
      connectWebSocket();
    }

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [open, user, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    try {
      const wsUrl = `${WEBSOCKET_URL}/ws/${user.id}`;
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);

        // Join the chat
        const joinMessage = {
          type: 'join_chat',
          data: {
            chat_id: chatId,
            item_id: itemId,
          }
        };
        websocketRef.current.send(JSON.stringify(joinMessage));
      };

      websocketRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      websocketRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'chat_message':
        if (data.chat_id === chatId) {
          setMessages(prev => [...prev, {
            id: Date.now(),
            sender_id: data.sender_id,
            message: data.message,
            timestamp: data.timestamp,
            isMine: data.sender_id === user.id,
          }]);
        }
        break;
      case 'chat_history':
        if (data.chat_id === chatId) {
          const historyMessages = data.messages.map(msg => ({
            id: Date.now() + Math.random(),
            sender_id: msg.sender_id,
            message: msg.message,
            timestamp: msg.timestamp,
            isMine: msg.sender_id === user.id,
          }));
          setMessages(historyMessages);
        }
        break;
      case 'typing_start':
        if (data.user_id !== user.id) {
          setIsTyping(true);
        }
        break;
      case 'typing_stop':
        if (data.user_id !== user.id) {
          setIsTyping(false);
        }
        break;
      case 'message_sent':
        // Message sent confirmation
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !websocketRef.current || !isConnected) {
      return;
    }

    const messageData = {
      type: 'chat_message',
      data: {
        recipient_id: recipientId,
        chat_id: chatId,
        message: newMessage.trim(),
        message_type: 'text',
      }
    };

    websocketRef.current.send(JSON.stringify(messageData));
    setNewMessage('');
  };

  const handleTyping = (isTyping) => {
    if (!websocketRef.current || !isConnected) {
      return;
    }

    const typingData = {
      type: isTyping ? 'typing_start' : 'typing_stop',
      data: {
        chat_id: chatId,
      }
    };

    websocketRef.current.send(JSON.stringify(typingData));
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) {
    return null;
  }

  return (
    <>
      {/* Chat Button */}
      <Fab
        color="primary"
        aria-label="chat"
        onClick={() => setOpen(true)}
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1000,
        }}
      >
        <ChatIcon />
      </Fab>

      {/* Chat Dialog */}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="sm"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            height: '600px',
            maxHeight: '80vh',
          }
        }}
      >
        <DialogTitle sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pb: 1
        }}>
          <Typography variant="h6" component="div">
            Chat
            {!isConnected && (
              <Typography variant="caption" color="error" sx={{ ml: 1 }}>
                (Disconnected)
              </Typography>
            )}
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={() => setOpen(false)}
            aria-label="close"
          >
            <Close />
          </IconButton>
        </DialogTitle>

        <Divider />

        <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
          {/* Messages Area */}
          <Box sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
          }}>
            {messages.length === 0 ? (
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'text.secondary',
              }}>
                <ChatIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="body1">
                  No messages yet. Start the conversation!
                </Typography>
              </Box>
            ) : (
              messages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: message.isMine ? 'flex-end' : 'flex-start',
                    mb: 1,
                  }}
                >
                  <Paper
                    sx={{
                      p: 1.5,
                      maxWidth: '70%',
                      bgcolor: message.isMine
                        ? theme.palette.primary.main
                        : theme.palette.grey[100],
                      color: message.isMine
                        ? 'white'
                        : 'text.primary',
                    }}
                  >
                    <Typography variant="body1">
                      {message.message}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        mt: 0.5,
                        opacity: 0.7,
                        textAlign: message.isMine ? 'right' : 'left',
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Paper>
                </Box>
              ))
            )}

            {isTyping && (
              <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                  Someone is typing...
                </Typography>
              </Box>
            )}

            <div ref={messagesEndRef} />
          </Box>

          {/* Message Input */}
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => {
                  setNewMessage(e.target.value);
                  handleTyping(e.target.value.length > 0);
                }}
                onKeyPress={handleKeyPress}
                disabled={!isConnected}
                size="small"
                multiline
                maxRows={3}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={sendMessage}
                disabled={!newMessage.trim() || !isConnected}
                sx={{ minWidth: 'auto', px: 2 }}
              >
                <Send />
              </Button>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Chat;