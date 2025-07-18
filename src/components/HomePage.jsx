import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const projects = [
  {
    title: 'Superhuman Friend',
    description: 'Your AI companion for meaningful conversations and assistance. Built with advanced LLMs and a focus on natural interactions.',
    link: '/chat',
    category: 'AI/ML',
    tags: ['React', 'Python', 'LangChain', 'OpenAI']
  },
  {
    title: 'RAG AI',
    description: 'Retrieval-Augmented Generation system that can analyze and answer questions about your documents with high accuracy.',
    link: '/rag',
    category: 'AI/ML',
    tags: ['Python', 'LangChain', 'Vector DB', 'PDF Processing']
  },
  {
    title: 'Code Assistant Pro',
    description: 'Intelligent coding companion that helps developers write better code faster, with real-time suggestions and code analysis.',
    link: '/code',
    category: 'Full Stack',
    tags: ['TypeScript', 'Node.js', 'GPT-4', 'MongoDB']
  },
  {
    title: 'Learning Lab',
    description: 'Adaptive learning platform that personalizes education paths using AI to match individual learning styles and goals.',
    link: '/learn',
    category: 'AI/ML',
    tags: ['Python', 'React', 'scikit-learn', 'FastAPI']
  }
];

function HomePage() {
  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <section className="relative overflow-hidden flex ">
        <div className="w-full px-8 py-24 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-[95%] mx-auto text-center"
          >
            <div className="space-y-8 text-left max-w-[80%] mx-auto">
            <p className="text-[#888] text-2xl sm:text-3xl hover:text-white transition-colors duration-300 mb-4 sm:mb-0">
            Hi, I'm Tarun
            </p>
              <br/>
              <p className="text-2xl md:text-3xl leading-relaxed text-gray-300">
                Welcome to my digital workshop — a curated collection of every project I've built, broken, rebuilt, and occasionally obsessed over at 2 AM. This site is a living archive of my journey as an LLM enthusiast, where ideas turn into code and curiosity fuels creation.
               
                Even if an idea begins as a half-baked thought, I believe in building it out — because done is better than perfect, and iteration is the real secret sauce. Expect frequent updates, new experiments, and a generous helping of large language models.
              
                If you're into GEN AI with purpose (and a pinch of personality), you're in the right place.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-16 px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-left mb-12 max-w-[80%] mx-auto"
        >
          <h2 className="text-5xl  text-white mb-6">
            Featured Projects
          </h2>
          <p className="text-xl text-gray-400">
            Explore my latest work in AI, web development, and cloud solutions. Each project represents
            a unique challenge and innovative solution.
          </p>
        </motion.div>

        <div className="max-w-[80%] mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project, index) => (
            <motion.div
              key={project.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 + 0.5 }}
            >
              <Link
                to={project.link}
                className="block group"
              >
                <div className="bg-[#111]/80 rounded-xl p-6 h-full border border-zinc-800/50 shadow-xl transform transition-all duration-200 hover:scale-[1.02] hover:shadow-2xl">
                  <h3 className="text-2xl font-semibold text-white mb-3">
                    {project.title}
                  </h3>
                  <p className="text-base text-gray-400 mb-6">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {project.tags.map(tag => (
                      <span key={tag} className="px-3 py-1 text-sm bg-[#222] rounded-full text-gray-300">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{project.category}</span>
                    <span className="text-green-400 flex items-center group-hover:translate-x-1 transition-transform">
                      View Project →
                    </span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

    </div>
  );
}

export default HomePage; 