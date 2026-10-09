// See klnr_pass.h. Adapted from OpenDLSS-NR demo/nr_pass.cpp (MIT, (c) 2026 maan, see LICENSE.OpenDLSS-NR).
#include "klnr_pass.h"

#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

#include "numeric.h"
#include "reference.h"

// The demo's NrParams (std140, 112 bytes; nr_preprocess.comp reads only this part) plus KLNR's two switches, which
// kl_composite.comp reads after it.
struct KlNrPass::ParamsBlock {
  uint32_t fullWidth, fullHeight, validWidth, validHeight;
  uint32_t sourceWidth, sourceHeight;
  float autoMask, paperWhite, colorStrength, intensity, localTone, localStructure, skinStructure, style;
  uint32_t historyValid, seed, nrEnabled, pad0;
  float blendScale, pad1;
  float styleExposure, styleContrast, styleGamma, styleSaturation;
  float styleHue, styleVibrance, styleStrength;
  uint32_t styleMode;
  uint32_t klSplit, klTest, klPad0, klPad1;
};

namespace {
// Without a model only the frame's round trip and the composite run, which need nothing beyond core Vulkan 1.2:
// a plain device, so the bridge also works (and can be tested) on GPUs that cannot run the network.
void createPlainDevice(VkInstance& instance, VkPhysicalDevice& physical, VkDevice& device, uint32_t& family) {
  if (volkInitialize() != VK_SUCCESS) throw std::runtime_error("vulkan-1.dll unavailable");
  VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
  app.pApplicationName = "klnr";
  app.apiVersion = VK_API_VERSION_1_2;
  VkInstanceCreateInfo instanceInfo{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
  instanceInfo.pApplicationInfo = &app;
  VK_CHECK(vkCreateInstance(&instanceInfo, nullptr, &instance));
  volkLoadInstance(instance);
  uint32_t count = 0;
  VK_CHECK(vkEnumeratePhysicalDevices(instance, &count, nullptr));
  if (!count) throw std::runtime_error("no Vulkan physical devices");
  std::vector<VkPhysicalDevice> devices(count);
  VK_CHECK(vkEnumeratePhysicalDevices(instance, &count, devices.data()));
  physical = devices[0];
  for (VkPhysicalDevice candidate : devices) {
    VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(candidate, &props);
    if (props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) { physical = candidate; break; }
  }
  uint32_t familyCount = 0;
  vkGetPhysicalDeviceQueueFamilyProperties(physical, &familyCount, nullptr);
  std::vector<VkQueueFamilyProperties> families(familyCount);
  vkGetPhysicalDeviceQueueFamilyProperties(physical, &familyCount, families.data());
  family = UINT32_MAX;
  for (uint32_t i = 0; i < familyCount && family == UINT32_MAX; ++i)
    if ((families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) && families[i].timestampValidBits) family = i;
  if (family == UINT32_MAX) throw std::runtime_error("no compute queue with timestamps");
  float priority = 1.0f;
  VkDeviceQueueCreateInfo queueInfo{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
  queueInfo.queueFamilyIndex = family; queueInfo.queueCount = 1; queueInfo.pQueuePriorities = &priority;
  VkPhysicalDeviceVulkan12Features f12{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};
  f12.bufferDeviceAddress = VK_TRUE;   // vk::Context makes every buffer with a device address
  VkPhysicalDeviceFeatures2 features{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
  features.pNext = &f12;
  VkDeviceCreateInfo deviceInfo{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
  deviceInfo.pNext = &features;
  deviceInfo.queueCreateInfoCount = 1; deviceInfo.pQueueCreateInfos = &queueInfo;
  VK_CHECK(vkCreateDevice(physical, &deviceInfo, nullptr, &device));
  volkLoadDevice(device);
}

double msSince(std::chrono::steady_clock::time_point t0) {
  return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
}
}  // namespace

KlNrPass::KlNrPass(const std::string& model, const std::string& baseDir, uint32_t width, uint32_t height) : base_(baseDir) {
  static_assert(sizeof(ParamsBlock) == 128, "std140 layout of kl_composite.comp's Params");
  kind_ = (model.empty() || model == "none") ? kNone : model == "zero" ? kZero : kDirectory;
  if (kind_ == kNone) {
    VkPhysicalDevice physical = VK_NULL_HANDLE;
    uint32_t family = 0;
    createPlainDevice(ownInstance_, physical, ownDevice_, family);
    context_ = std::make_unique<vk::Context>(ownInstance_, physical, ownDevice_, family, 0);
  } else {
    context_ = std::make_unique<vk::Context>();   // its own instance and device with the NR kernels' features
  }
  device_ = context_->device();
  if (kind_ != kNone) {
    model_ = std::make_unique<nr::Model>(*context_, kind_ == kZero ? std::string(nr::Model::kZeroModel) : model, false);
    kernels_ = std::make_unique<nr::Kernels>(*context_, base_ + "/spv");   // PTX from spv/../ptx
    kernels_->setSiluTable(ref::siluTable());
    const nr::Tensor& blend = model_->tensor(70, 0, "blend_scale");
    blendScale_ = blend.byteLength >= 2 ? num::f16ToF32((uint16_t)(blend.bytes[0] | (blend.bytes[1] << 8))) : 1.0f;
  }

  VkSamplerCreateInfo samplerInfo{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
  samplerInfo.magFilter = samplerInfo.minFilter = VK_FILTER_LINEAR;
  samplerInfo.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
  samplerInfo.addressModeU = samplerInfo.addressModeV = samplerInfo.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
  samplerInfo.maxLod = 1.0f;
  VK_CHECK(vkCreateSampler(device_, &samplerInfo, nullptr, &linearSampler_));
  samplerInfo.magFilter = samplerInfo.minFilter = VK_FILTER_NEAREST;
  VK_CHECK(vkCreateSampler(device_, &samplerInfo, nullptr, &nearestSampler_));
  for (vk::Buffer& b : params_)
    b = context_->createBuffer(sizeof(ParamsBlock), false, "klnr params", VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT);

  VkDescriptorSetLayoutBinding bindings[7] = {
      {0, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {1, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {2, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {3, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {4, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {5, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr},
      {6, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr}};
  VkDescriptorSetLayoutCreateInfo layoutInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
  layoutInfo.bindingCount = 7; layoutInfo.pBindings = bindings;
  VK_CHECK(vkCreateDescriptorSetLayout(device_, &layoutInfo, nullptr, &setLayout_));
  VkPipelineLayoutCreateInfo plInfo{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
  plInfo.setLayoutCount = 1; plInfo.pSetLayouts = &setLayout_;
  VK_CHECK(vkCreatePipelineLayout(device_, &plInfo, nullptr, &layout_));
  if (model_) preprocess_ = computePipeline(base_ + "/shaders/nr_preprocess.spv");
  composite_ = computePipeline(base_ + "/shaders/kl_composite.spv");

  VkDescriptorPoolSize poolSizes[4] = {{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 12}, {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 4},
                                       {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 4}, {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 8}};
  VkDescriptorPoolCreateInfo poolInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
  poolInfo.maxSets = 4; poolInfo.poolSizeCount = 4; poolInfo.pPoolSizes = poolSizes;
  VK_CHECK(vkCreateDescriptorPool(device_, &poolInfo, nullptr, &pool_));
  VkDescriptorSetAllocateInfo alloc{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
  alloc.descriptorPool = pool_; alloc.descriptorSetCount = 1; alloc.pSetLayouts = &setLayout_;
  for (int h = 0; h < 2; ++h)
    for (int k = 0; k < 2; ++k) VK_CHECK(vkAllocateDescriptorSets(device_, &alloc, &sets_[h][k]));
  for (VkQueryPool& q : queries_) q = context_->createTimestampPool(kStampCount);

  VkCommandPoolCreateInfo cmdPoolInfo{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
  cmdPoolInfo.queueFamilyIndex = context_->queueFamily();
  VK_CHECK(vkCreateCommandPool(device_, &cmdPoolInfo, nullptr, &secondaryPool_));
  cmdPoolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
  VK_CHECK(vkCreateCommandPool(device_, &cmdPoolInfo, nullptr, &primaryPool_));
  VkCommandBufferAllocateInfo allocate{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
  allocate.commandPool = secondaryPool_; allocate.level = VK_COMMAND_BUFFER_LEVEL_SECONDARY; allocate.commandBufferCount = 4;
  VK_CHECK(vkAllocateCommandBuffers(device_, &allocate, &secondary_[0][0]));
  allocate.commandPool = primaryPool_; allocate.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; allocate.commandBufferCount = 1;
  VK_CHECK(vkAllocateCommandBuffers(device_, &allocate, &primary_));
  VkFenceCreateInfo fenceInfo{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
  VK_CHECK(vkCreateFence(device_, &fenceInfo, nullptr, &fence_));
  createSized(width, height);
}

KlNrPass::~KlNrPass() {
  if (!device_) return;
  vkDeviceWaitIdle(device_);
  destroySized();
  vkDestroyFence(device_, fence_, nullptr);
  vkDestroyCommandPool(device_, primaryPool_, nullptr);
  vkDestroyCommandPool(device_, secondaryPool_, nullptr);
  for (VkQueryPool q : queries_) vkDestroyQueryPool(device_, q, nullptr);
  vkDestroyDescriptorPool(device_, pool_, nullptr);
  if (preprocess_) vkDestroyPipeline(device_, preprocess_, nullptr);
  vkDestroyPipeline(device_, composite_, nullptr);
  vkDestroyPipelineLayout(device_, layout_, nullptr);
  vkDestroyDescriptorSetLayout(device_, setLayout_, nullptr);
  for (vk::Buffer& b : params_) context_->destroyBuffer(b);
  vkDestroySampler(device_, linearSampler_, nullptr);
  vkDestroySampler(device_, nearestSampler_, nullptr);
  graph_.reset();
  kernels_.reset();
  model_.reset();
  context_.reset();
  if (ownDevice_) vkDestroyDevice(ownDevice_, nullptr);
  if (ownInstance_) vkDestroyInstance(ownInstance_, nullptr);
}

KlNrPass::Image KlNrPass::createImage(uint32_t width, uint32_t height, VkFormat format, VkImageUsageFlags usage) {
  Image image; image.format = format;
  VkImageCreateInfo info{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
  info.imageType = VK_IMAGE_TYPE_2D; info.format = format; info.extent = {width, height, 1};
  info.mipLevels = 1; info.arrayLayers = 1; info.samples = VK_SAMPLE_COUNT_1_BIT; info.tiling = VK_IMAGE_TILING_OPTIMAL;
  info.usage = usage; info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
  VK_CHECK(vkCreateImage(device_, &info, nullptr, &image.image));
  VkMemoryRequirements req; vkGetImageMemoryRequirements(device_, image.image, &req);
  VkPhysicalDeviceMemoryProperties props; vkGetPhysicalDeviceMemoryProperties(context_->physical(), &props);
  uint32_t type = UINT32_MAX;
  for (uint32_t i = 0; i < props.memoryTypeCount; ++i)
    if ((req.memoryTypeBits & (1u << i)) && (props.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)) { type = i; break; }
  if (type == UINT32_MAX) throw std::runtime_error("no device-local memory for an image");
  VkMemoryAllocateInfo alloc{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO}; alloc.allocationSize = req.size; alloc.memoryTypeIndex = type;
  VK_CHECK(vkAllocateMemory(device_, &alloc, nullptr, &image.memory));
  VK_CHECK(vkBindImageMemory(device_, image.image, image.memory, 0));
  VkImageViewCreateInfo viewInfo{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
  viewInfo.image = image.image; viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D; viewInfo.format = format;
  viewInfo.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
  VK_CHECK(vkCreateImageView(device_, &viewInfo, nullptr, &image.view));
  return image;
}

void KlNrPass::destroyImage(Image& image) {
  if (image.view) vkDestroyImageView(device_, image.view, nullptr);
  if (image.image) vkDestroyImage(device_, image.image, nullptr);
  if (image.memory) vkFreeMemory(device_, image.memory, nullptr);
  image = Image{};
}

void KlNrPass::imageBarrier(VkCommandBuffer commands, VkImage image, VkImageLayout from, VkImageLayout to, VkPipelineStageFlags srcStage,
                            VkAccessFlags srcAccess, VkPipelineStageFlags dstStage, VkAccessFlags dstAccess) {
  VkImageMemoryBarrier barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
  barrier.srcAccessMask = srcAccess; barrier.dstAccessMask = dstAccess;
  barrier.oldLayout = from; barrier.newLayout = to;
  barrier.srcQueueFamilyIndex = barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
  barrier.image = image; barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
  vkCmdPipelineBarrier(commands, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &barrier);
}

VkPipeline KlNrPass::computePipeline(const std::string& spv) {
  VkShaderModule module = context_->loadShaderModule(spv);   // owned by the Context
  VkComputePipelineCreateInfo info{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
  info.stage = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_COMPUTE_BIT, module, "main", nullptr};
  info.layout = layout_;
  VkPipeline pipeline;
  VK_CHECK(vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &info, nullptr, &pipeline));
  return pipeline;
}

void KlNrPass::createSized(uint32_t width, uint32_t height) {
  width_ = width; height_ = height;
  geometry_ = nr::Geometry::fromValid(width, height);
  if (model_) {
    graph_ = std::make_unique<nr::Graph>(*context_, *model_, *kernels_, geometry_, nr::Graph::Options{});
    features_ = graph_->allocate("input features", geometry_.fullWidth * geometry_.fullHeight, 16, nr::Format::F32);
    // warm-up: the graph allocates its activations at the first record, and the driver loads every pipeline and
    // CUDA module now instead of on the first game frame
    context_->fillZero(features_->buffer);
    VkCommandBuffer commands = context_->beginCommands();
    graph_->record(commands, *features_);
    context_->endAndSubmit(commands, true);
  }
  const VkImageUsageFlags storage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
  color_ = createImage(width, height, VK_FORMAT_B8G8R8A8_SRGB, VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT);
  motion_ = createImage(width, height, VK_FORMAT_R16G16B16A16_SFLOAT, storage);
  for (Image& h : history_) h = createImage(width, height, VK_FORMAT_R16G16B16A16_SFLOAT, storage);
  output_ = createImage(width, height, VK_FORMAT_R8G8B8A8_UNORM, storage | VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
  upload_ = context_->createBuffer((VkDeviceSize)width * height * 4, true, "frame upload");
  readback_ = context_->createBuffer((VkDeviceSize)width * height * 4, true, "frame readback");
  {
    VkCommandBuffer commands = context_->beginCommands();
    VkImageSubresourceRange range{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    imageBarrier(commands, color_.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, 0,
                 VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
    VkClearColorValue zero{};
    vkCmdClearColorImage(commands, color_.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &zero, 1, &range);
    imageBarrier(commands, color_.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_PIPELINE_STAGE_TRANSFER_BIT,
                 VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT);
    // the storage images live in GENERAL for their whole life
    // No motion vectors yet (Dog Days renders none): every pixel's history is at the same pixel and on screen.
    // GUESS until camera reprojection exists: right for a still camera; when it moves, the network's own per-pixel
    // blend weight is all that keeps the stale history out.
    VkClearColorValue still{};
    still.float32[2] = 1.0f;
    for (Image* image : {&motion_, &history_[0], &history_[1], &output_}) {
      imageBarrier(commands, image->image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, 0,
                   VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
      vkCmdClearColorImage(commands, image->image, VK_IMAGE_LAYOUT_GENERAL, image == &motion_ ? &still : &zero, 1, &range);
    }
    VkMemoryBarrier memory{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    memory.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; memory.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
    vkCmdPipelineBarrier(commands, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 1, &memory, 0, nullptr, 0, nullptr);
    context_->endAndSubmit(commands, true);
  }
  updateComputeSets();
  buildComputeCommands();
  framesSinceReset_ = 0;
}

void KlNrPass::destroySized() {
  VK_CHECK(vkDeviceWaitIdle(device_));
  VK_CHECK(vkResetCommandPool(device_, secondaryPool_, 0));
  for (Image* image : {&color_, &motion_, &history_[0], &history_[1], &output_}) destroyImage(*image);
  context_->destroyBuffer(upload_);
  context_->destroyBuffer(readback_);
  features_ = nullptr;
  graph_.reset();
}

void KlNrPass::resize(uint32_t width, uint32_t height) {
  if (width == width_ && height == height_) return;
  destroySized();
  createSized(width, height);
}

void KlNrPass::updateComputeSets() {
  const vk::Buffer& dummy = context_->dummyBuffer();
  for (int h = 0; h < 2; ++h) {
    for (int k = 0; k < 2; ++k) {
      VkDescriptorImageInfo color{nearestSampler_, color_.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
      VkDescriptorImageInfo prev{linearSampler_, history_[h].view, VK_IMAGE_LAYOUT_GENERAL};
      VkDescriptorImageInfo motion{nearestSampler_, motion_.view, VK_IMAGE_LAYOUT_GENERAL};
      VkBuffer data = dummy.buffer;
      if (graph_) data = k == 0 ? features_->buffer.buffer : graph_->head().buffer.buffer;
      VkDescriptorBufferInfo buffer{data, 0, VK_WHOLE_SIZE};
      VkDescriptorBufferInfo params{params_[h].buffer, 0, sizeof(ParamsBlock)};
      VkDescriptorImageInfo out{VK_NULL_HANDLE, output_.view, VK_IMAGE_LAYOUT_GENERAL};
      VkDescriptorImageInfo next{VK_NULL_HANDLE, history_[1 - h].view, VK_IMAGE_LAYOUT_GENERAL};
      VkWriteDescriptorSet writes[7]{};
      for (int i = 0; i < 7; ++i) {
        writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET; writes[i].dstSet = sets_[h][k]; writes[i].dstBinding = i;
        writes[i].descriptorCount = 1;
      }
      writes[0].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER; writes[0].pImageInfo = &color;
      writes[1].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER; writes[1].pImageInfo = &prev;
      writes[2].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER; writes[2].pImageInfo = &motion;
      writes[3].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; writes[3].pBufferInfo = &buffer;
      writes[4].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER; writes[4].pBufferInfo = &params;
      writes[5].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE; writes[5].pImageInfo = &out;
      writes[6].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE; writes[6].pImageInfo = &next;
      vkUpdateDescriptorSets(device_, 7, writes, 0, nullptr);
    }
  }
}

// Recorded once per size: the network's ~250 dispatches cost milliseconds of CPU to record and nothing in them
// changes between frames (the parameters are a UBO written in the command stream, the history alternates by parity).
void KlNrPass::buildComputeCommands() {
  VK_CHECK(vkResetCommandPool(device_, secondaryPool_, 0));
  for (uint32_t h = 0; h < 2; ++h) {
    if (graph_) context_->resetDescriptorPool(h);   // the graph's descriptor sets of this parity live in pool h
    for (int enabled = 0; enabled < 2; ++enabled) {
      VkCommandBuffer commands = secondary_[h][enabled];
      VkCommandBufferInheritanceInfo inheritance{VK_STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_INFO};
      VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
      begin.flags = VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT;
      begin.pInheritanceInfo = &inheritance;
      VK_CHECK(vkBeginCommandBuffer(commands, &begin));
      const bool network = enabled && graph_;
      if (network) {
        vkCmdBindPipeline(commands, VK_PIPELINE_BIND_POINT_COMPUTE, preprocess_);
        vkCmdBindDescriptorSets(commands, VK_PIPELINE_BIND_POINT_COMPUTE, layout_, 0, 1, &sets_[h][0], 0, nullptr);
        vkCmdDispatch(commands, (geometry_.fullWidth + 7) / 8, (geometry_.fullHeight + 7) / 8, 1);
        context_->computeBarrier(commands);
      }
      vkCmdWriteTimestamp(commands, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, queries_[h], kPreprocessEnd);
      if (network) graph_->record(commands, *features_);
      vkCmdWriteTimestamp(commands, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, queries_[h], kNetworkEnd);
      vkCmdBindPipeline(commands, VK_PIPELINE_BIND_POINT_COMPUTE, composite_);
      vkCmdBindDescriptorSets(commands, VK_PIPELINE_BIND_POINT_COMPUTE, layout_, 0, 1, &sets_[h][1], 0, nullptr);
      vkCmdDispatch(commands, (width_ + 7) / 8, (height_ + 7) / 8, 1);
      VkMemoryBarrier memory{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
      memory.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT; memory.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_TRANSFER_READ_BIT;
      vkCmdPipelineBarrier(commands, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT | VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                           0, 1, &memory, 0, nullptr, 0, nullptr);
      vkCmdWriteTimestamp(commands, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, queries_[h], kCompositeEnd);
      VK_CHECK(vkEndCommandBuffer(commands));
    }
  }
}

void KlNrPass::process(uint8_t* bgra, uint32_t pitch, const KlControls& c, KlTimings& t) {
  const auto t0 = std::chrono::steady_clock::now();
  const uint32_t row = width_ * 4;
  uint8_t* up = (uint8_t*)upload_.mapped;
  for (uint32_t y = 0; y < height_; ++y) memcpy(up + (size_t)y * row, bgra + (size_t)y * pitch, row);
  if (c.resetHistory) framesSinceReset_ = 0;
  const uint32_t h = frames_ & 1u;
  const bool network = c.enabled && graph_;

  ParamsBlock block{};
  block.fullWidth = geometry_.fullWidth; block.fullHeight = geometry_.fullHeight;
  block.validWidth = width_; block.validHeight = height_;
  block.sourceWidth = width_; block.sourceHeight = height_;
  block.autoMask = c.autoMask ? 1.0f : 0.0f;
  block.paperWhite = c.paperWhite; block.colorStrength = c.colorStrength; block.intensity = c.intensity;
  block.localTone = c.localTone; block.localStructure = c.localStructure; block.skinStructure = c.skinStructure;
  block.style = (float)c.style;
  block.historyValid = (c.temporal && framesSinceReset_ > 0) ? 1u : 0u;
  block.seed = c.temporal ? frames_ : 0u;   // a still frame without the temporal loop keeps one noise pattern
  block.nrEnabled = network ? 1u : 0u;
  block.blendScale = blendScale_;
  block.styleGamma = 1.0f; block.styleVibrance = 1.0f; block.styleStrength = 1.0f;
  block.klSplit = c.split ? 1u : 0u;
  block.klTest = c.test ? 1u : 0u;

  VK_CHECK(vkResetCommandBuffer(primary_, 0));
  VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
  begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
  VK_CHECK(vkBeginCommandBuffer(primary_, &begin));
  VkCommandBuffer cb = primary_;
  vkCmdResetQueryPool(cb, queries_[h], 0, kStampCount);
  vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, queries_[h], kStart);
  // the frame in: host buffer -> the sRGB image the shaders sample (so they read linear values)
  imageBarrier(cb, color_.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0,
               VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
  VkBufferImageCopy region{};
  region.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
  region.imageExtent = {width_, height_, 1};
  vkCmdCopyBufferToImage(cb, upload_.buffer, color_.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
  imageBarrier(cb, color_.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_PIPELINE_STAGE_TRANSFER_BIT,
               VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT);
  vkCmdUpdateBuffer(cb, params_[h].buffer, 0, sizeof(ParamsBlock), &block);
  VkMemoryBarrier paramsBarrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
  paramsBarrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; paramsBarrier.dstAccessMask = VK_ACCESS_UNIFORM_READ_BIT;
  vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 1, &paramsBarrier, 0, nullptr, 0, nullptr);
  vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, queries_[h], kUploadEnd);
  // preprocess -> network -> composite (pre-recorded)
  vkCmdExecuteCommands(cb, 1, &secondary_[h][network ? 1 : 0]);
  // the result out
  imageBarrier(cb, output_.image, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
               VK_ACCESS_SHADER_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_READ_BIT);
  vkCmdCopyImageToBuffer(cb, output_.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, readback_.buffer, 1, &region);
  imageBarrier(cb, output_.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL, VK_PIPELINE_STAGE_TRANSFER_BIT,
               VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_WRITE_BIT | VK_ACCESS_SHADER_READ_BIT);
  VkBufferMemoryBarrier toHost{VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER};
  toHost.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; toHost.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
  toHost.srcQueueFamilyIndex = toHost.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
  toHost.buffer = readback_.buffer; toHost.size = VK_WHOLE_SIZE;
  vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 0, nullptr, 1, &toHost, 0, nullptr);
  vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, queries_[h], kDownloadEnd);
  VK_CHECK(vkEndCommandBuffer(cb));

  VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
  submit.commandBufferCount = 1; submit.pCommandBuffers = &cb;
  VK_CHECK(vkResetFences(device_, 1, &fence_));
  VK_CHECK(vkQueueSubmit(context_->queue(), 1, &submit, fence_));
  VkResult wait = vkWaitForFences(device_, 1, &fence_, VK_TRUE, 5ull * 1000 * 1000 * 1000);
  if (wait != VK_SUCCESS) throw std::runtime_error("frame did not finish within 5 s (VkResult " + std::to_string((int)wait) + ")");

  uint64_t ticks[kStampCount];
  if (vkGetQueryPoolResults(device_, queries_[h], 0, kStampCount, sizeof(ticks), ticks, 8, VK_QUERY_RESULT_64_BIT) == VK_SUCCESS) {
    const double period = context_->timestampPeriodNs() * 1e-6;
    auto span = [&](Stamp a, Stamp b) { return (double)(ticks[b] - ticks[a]) * period; };
    t.uploadMs = span(kStart, kUploadEnd);
    t.preprocessMs = span(kUploadEnd, kPreprocessEnd);
    t.networkMs = span(kPreprocessEnd, kNetworkEnd);
    t.compositeMs = span(kNetworkEnd, kCompositeEnd);
    t.downloadMs = span(kCompositeEnd, kDownloadEnd);
    t.gpuMs = span(kStart, kDownloadEnd);
  }
  const uint8_t* down = (const uint8_t*)readback_.mapped;
  for (uint32_t y = 0; y < height_; ++y) memcpy(bgra + (size_t)y * pitch, down + (size_t)y * row, row);
  ++frames_;
  ++framesSinceReset_;
  t.hostMs = msSince(t0);
}
