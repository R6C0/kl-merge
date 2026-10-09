// KLNR's frame pass: one game frame (BGRA8, display-referred sRGB) in, the same frame through OpenDLSS-NR's network
// out. Adapted from OpenDLSS-NR demo/nr_pass (MIT, (c) 2026 maan, see LICENSE.OpenDLSS-NR): the preprocess, the
// network graph, the temporal composite and the pre-recorded command buffers are the demo's; the renderer interop is
// replaced by an upload / readback of host memory, the device is the helper's own (vk::Context), the model is
// optional (none: the frame makes the round trip only; "zero": synthetic zero weights, full network cost, no change),
// and there are no motion vectors yet (the motion image says "the history is at the same pixel").
#pragma once
#include <memory>
#include <string>
#include <vector>

#include "kernels.h"
#include "nr_graph.h"
#include "nr_model.h"
#include "vk_context.h"

struct KlControls {
  bool enabled = true;        // run the network (when there is a model)
  bool temporal = true;       // blend with the previous output
  bool resetHistory = false;  // this frame has no history (a cut, a load)
  bool split = false;         // left half untouched (A/B)
  bool test = false;          // right half grey: shows the round trip on screen
  bool autoMask = true;
  float intensity = 1.0f, localTone = 1.0f, localStructure = 1.0f, skinStructure = -1.0f;
  float paperWhite = 1.0f, colorStrength = 1.0f;
  int style = 0;              // 0 off, 1 natural, 2 cinematic
};

struct KlTimings {
  double uploadMs = 0, preprocessMs = 0, networkMs = 0, compositeMs = 0, downloadMs = 0, gpuMs = 0, hostMs = 0;
  bool discarded = false;   // the network's result was not usable (takeNotes() says why): the frame is left as it came
};

class KlNrPass {
 public:
  enum ModelKind { kNone = 0, kZero = 1, kDirectory = 2 };
  // model: "" or "none", "zero", or a model directory (manifest.json + model/ stage files, supplied by the user).
  // baseDir holds spv/ (the network's kernels), ptx/ and shaders/ (nr_preprocess.spv, kl_composite.spv).
  KlNrPass(const std::string& model, const std::string& baseDir, uint32_t width, uint32_t height);
  ~KlNrPass();

  void resize(uint32_t width, uint32_t height);
  // In place: `bgra` holds width x height pixels, `pitch` bytes per row.
  void process(uint8_t* bgra, uint32_t pitch, const KlControls& controls, KlTimings& timings);

  ModelKind modelKind() const { return kind_; }
  const std::string& deviceName() const { return context_->deviceName(); }
  uint32_t width() const { return width_; }
  uint32_t height() const { return height_; }
  float blendScale() const { return blendScale_; }
  // Where the CPU reads results from: cached host memory (fast) or not (an order of magnitude slower on NVIDIA).
  bool readbackCached() const { return readbackCached_; }
  // What happened since the last call that deserves a log line (watchdog timeouts, rebuilds); empties the list.
  std::vector<std::string> takeNotes() { std::vector<std::string> notes; notes.swap(notes_); return notes; }

 private:
  struct Image {
    VkImage image = VK_NULL_HANDLE; VkDeviceMemory memory = VK_NULL_HANDLE; VkImageView view = VK_NULL_HANDLE;
    VkFormat format = VK_FORMAT_UNDEFINED;
  };
  enum Stamp { kStart = 0, kUploadEnd = 1, kPreprocessEnd = 2, kNetworkEnd = 3, kCompositeEnd = 4, kDownloadEnd = 5, kStampCount = 6 };
  struct ParamsBlock;

  Image createImage(uint32_t width, uint32_t height, VkFormat format, VkImageUsageFlags usage);
  void destroyImage(Image& image);
  void imageBarrier(VkCommandBuffer commands, VkImage image, VkImageLayout from, VkImageLayout to, VkPipelineStageFlags srcStage,
                    VkAccessFlags srcAccess, VkPipelineStageFlags dstStage, VkAccessFlags dstAccess);
  VkPipeline computePipeline(const std::string& spv);
  vk::Buffer createReadback(VkDeviceSize size);
  void createSized(uint32_t width, uint32_t height);
  void destroySized();
  void updateComputeSets();
  void buildComputeCommands();
  void createKernels(uint64_t pixels);
  // The network's chained-wait watchdog (see nr::Kernels::chainTimeouts): true = the last submission was wrong.
  bool chainTimedOut(const char* when);

  std::string base_;
  ModelKind kind_ = kNone;
  VkInstance ownInstance_ = VK_NULL_HANDLE;   // the plain device of the no-model mode (any Vulkan GPU)
  VkDevice ownDevice_ = VK_NULL_HANDLE;
  std::unique_ptr<vk::Context> context_;
  std::unique_ptr<nr::Model> model_;
  std::unique_ptr<nr::Kernels> kernels_;
  std::unique_ptr<nr::Graph> graph_;
  nr::Geometry geometry_{};
  nr::Activation* features_ = nullptr;
  VkDevice device_ = VK_NULL_HANDLE;
  uint32_t width_ = 0, height_ = 0;
  float blendScale_ = 1.0f;

  Image color_, motion_, history_[2], output_;
  vk::Buffer upload_, readback_, params_[2];
  VkSampler linearSampler_ = VK_NULL_HANDLE, nearestSampler_ = VK_NULL_HANDLE;
  VkDescriptorSetLayout setLayout_ = VK_NULL_HANDLE;
  VkPipelineLayout layout_ = VK_NULL_HANDLE;
  VkPipeline preprocess_ = VK_NULL_HANDLE, composite_ = VK_NULL_HANDLE;
  VkDescriptorPool pool_ = VK_NULL_HANDLE;
  VkDescriptorSet sets_[2][2]{};          // [history parity][0 preprocess, 1 composite]
  VkCommandPool secondaryPool_ = VK_NULL_HANDLE, primaryPool_ = VK_NULL_HANDLE;
  VkCommandBuffer secondary_[2][2]{};     // [history parity][network off, on]
  VkCommandBuffer primary_ = VK_NULL_HANDLE;
  VkFence fence_ = VK_NULL_HANDLE;
  VkQueryPool queries_[2]{};
  uint32_t frames_ = 0, framesSinceReset_ = 0;
  bool readbackCached_ = false, readbackCoherent_ = true;
  uint64_t kernelPixels_ = 0;   // the frame size the kernels' split-K scratch was sized for (it never grows)
  std::vector<std::string> notes_;
};
