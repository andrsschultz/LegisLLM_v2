export default function EinfuehrungsvideoPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-5xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-900">LegisLLM – Einführungsvideo</h1>
          <p className="text-slate-500 text-sm mt-1">KI-gestützte Legistik</p>
        </div>

        <div className="rounded-xl overflow-hidden shadow-lg aspect-video">
          <iframe
            src="https://www.youtube-nocookie.com/embed/nSULTYej9nk"
            title="LegisLLM Einführungsvideo"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full h-full"
          />
        </div>
      </div>
    </div>
  );
}
