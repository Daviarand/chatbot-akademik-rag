<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Akademik Informatika UII</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 h-screen flex flex-col">

    <!-- Header -->
    <header class="bg-blue-900 text-white p-4 shadow-md">
        <h1 class="text-xl font-bold text-center">Chatbot Layanan Akademik Informatika UII</h1>
    </header>

    <!-- Chat Container -->
    <main id="chat-container" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Welcome Message -->
        <div class="flex justify-start">
            <div class="bg-white p-3 rounded-lg shadow-sm max-w-[80%]">
                Halo! Saya asisten akademik Informatika UII. Ada yang bisa saya bantu terkait info KRS, syarat lulus, atau beasiswa?
            </div>
        </div>
    </main>

    <!-- Input Area -->
    <footer class="bg-white p-4 border-t">
        <form id="chat-form" class="flex space-x-2">
            <input type="text" id="user-input" placeholder="Ketik pertanyaan Anda di sini..." class="flex-1 border rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded-full hover:bg-blue-700 transition">Kirim</button>
        </form>
    </footer>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const chatForm = document.getElementById('chat-form');
        const userInput = document.getElementById('user-input');

        function addMessage(text, isUser = false) {
            const div = document.createElement('div');
            div.className = isUser ? 'flex justify-end' : 'flex justify-start';
            
            const innerDiv = document.createElement('div');
            innerDiv.className = isUser 
                ? 'bg-blue-500 text-white p-3 rounded-lg shadow-sm max-w-[80%]' 
                : 'bg-white p-3 rounded-lg shadow-sm max-w-[80%]';
            innerDiv.innerText = text;
            
            div.appendChild(innerDiv);
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = userInput.value.trim();
            if (!query) return;

            addMessage(query, true);
            userInput.value = '';

            // Tampilkan loading
            const loadingId = 'loading-' + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.id = loadingId;
            loadingDiv.className = 'flex justify-start';
            loadingDiv.innerHTML = '<div class="bg-gray-200 p-3 rounded-lg shadow-sm animate-pulse">Sedang berpikir...</div>';
            chatContainer.appendChild(loadingDiv);

            try {
                const response = await fetch('http://localhost:5000/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                document.getElementById(loadingId).remove();
                
                if (data.answer) {
                    addMessage(data.answer);
                } else {
                    addMessage('Maaf, terjadi kesalahan saat menghubungi server.');
                }
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessage('Maaf, tidak dapat terhubung ke server Flask.');
                console.error(error);
            }
        });
    </script>
</body>
</html>
