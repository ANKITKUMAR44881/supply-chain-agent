import Head from 'next/head'
import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [response, setResponse] = useState<string>('');

  const handleSubmit = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('http://localhost:8000/run_ctb/', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    setResponse(JSON.stringify(data));
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <Head>
        <title>Supply Chain Agent</title>
      </Head>
      <h1 className="text-2xl font-bold mb-4">Upload CTB Excel File</h1>
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button onClick={handleSubmit} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        Run Agent
      </button>
      <pre className="mt-6 p-4 bg-gray-100 w-full max-w-xl overflow-x-auto">
        {response || 'Results will show here...'}
      </pre>
    </div>
  );
}
