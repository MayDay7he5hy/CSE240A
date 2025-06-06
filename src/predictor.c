//========================================================//
//  predictor.c                                           //
//  Source file for the Branch Predictor                  //
//                                                        //
//  Implement the various branch predictors below as      //
//  described in the README                               //
//========================================================//
#include <stdio.h>
#include <string.h>
#include <stdlib.h> // For malloc, abs
#include "predictor.h"

//
// TODO:Student Information
//
const char *studentName = "Juncheng Gao";
const char *studentID   = "A69032166";
const char *email       = "jug045@ucsd.edu";

//------------------------------------//
//      Predictor Configuration       //
//------------------------------------//

// Handy Global for use in output routines
const char *bpName[4] = { "Static", "Gshare",
                          "Tournament", "Custom" };

// Gshare, Tournament, and Custom predictors use these fields
int ghistoryBits; // Number of bits used for Global History (for Gshare/Tournament)
int lhistoryBits; // Number of bits used for Local History (for Tournament)
int pcIndexBits;  // Number of bits used for PC index (for Tournament)
int bpType;       // Branch Prediction Type
int verbose;

//------------------------------------//
//      Predictor Data Structures     //
//------------------------------------//

// Gshare predictor
uint32_t ghistory;
uint8_t *gshareBHT;

// Tournament predictor
uint32_t *localPHT;
uint8_t *localBHT;
uint8_t *choicePT;
uint32_t globalhistory_tour;
uint8_t *globalBHT;
uint8_t localOutcome, globalOutcome;

//== CUSTOM: Perceptron Predictor Data Structures ==//
// Perceptron的核心思想：将分支预测视为一个线性分类问题。
// 全局历史的每一位都是一个特征，每个特征有一个权重。
// 通过计算权重的加权和来决定预测结果。

// 1. 超参数 (这些值是优化的关键, 需要通过实验来调整)
#define PERCEPTRON_HISTORY_LENGTH 25 // 感知机使用的全局历史长度。这是一个很好的起点。
#define NUM_WEIGHT_TABLES 163        // 权重表的数量, 用于减少PC之间的冲突。使用一个素数可能有助于哈希分布。
#define MAX_WEIGHT 127               // int8_t能存储的最大正权重
#define MIN_WEIGHT -128              // int8_t能存储的最大负权重

// 2. 学习阈值 Theta
// theta = floor(1.93 * H + 14), H是历史长度.
// 只有在 |y_out| <= theta 时才进行训练, 这可以防止在"高置信度"的正确预测上过度训练。
const int LEARNING_THRESHOLD = (int)(1.93 * PERCEPTRON_HISTORY_LENGTH + 14);

// 3. 数据结构
long long perceptron_ghistory; // 使用64位整数存储长历史
// 权重表: [表索引][历史位索引+1]。+1是为偏置(bias)权重保留位置。
int8_t weights[NUM_WEIGHT_TABLES][PERCEPTRON_HISTORY_LENGTH + 1];

//------------------------------------//
//        Helper Functions            //
//------------------------------------//
void shift_prediction(uint8_t *saturate, uint8_t outcome) {
    if (outcome == NOTTAKEN) {
        if (*saturate != SN) (*saturate)--;
    } else {
        if (*saturate != ST) (*saturate)++;
    }
}

//------------------------------------//
//        Predictor Functions         //
//------------------------------------//

// Initialize the predictor
void init_predictor()
{
  switch (bpType) {
    case STATIC:
      return;
    case GSHARE:
      ghistory = 0;
      gshareBHT = (uint8_t*)malloc((1 << ghistoryBits) * sizeof(uint8_t));
      memset(gshareBHT, WN, (1 << ghistoryBits));
      break;
    case TOURNAMENT:
      // Local History Table
      localPHT = (uint32_t*)malloc((1 << pcIndexBits) * sizeof(uint32_t));
      memset(localPHT, 0, (1 << pcIndexBits) * sizeof(uint32_t));
      
      // Local Branch History Table
      localBHT = (uint8_t*)malloc((1 << lhistoryBits) * sizeof(uint8_t));
      memset(localBHT, WN, (1 << lhistoryBits));
      
      // Global Branch History Table
      globalBHT = (uint8_t*)malloc((1 << ghistoryBits) * sizeof(uint8_t));
      memset(globalBHT, WN, (1 << ghistoryBits));
      
      // Choice Predictor Table
      choicePT = (uint8_t*)malloc((1 << ghistoryBits) * sizeof(uint8_t));
      memset(choicePT, WN, (1 << ghistoryBits)); // Prefer Global at start

      globalhistory_tour = 0;
      break;
    case CUSTOM:
      printf("Initializing CUSTOM Perceptron Predictor\n");
      printf("History Length: %d, Weight Tables: %d, Learning Threshold: %d\n",
             PERCEPTRON_HISTORY_LENGTH, NUM_WEIGHT_TABLES, LEARNING_THRESHOLD);
      perceptron_ghistory = 0;
      // 初始化所有权重为0
      memset(weights, 0, sizeof(weights));
      break;
    default:
      break;
  }
}

// Make a prediction for conditional branch instruction at PC 'pc'
uint8_t make_prediction(uint32_t pc)
{
  uint32_t gBHT_idx;

  switch (bpType) {
    case STATIC:
      return TAKEN;
    case GSHARE:
      gBHT_idx = (ghistory ^ (pc & ((1<<ghistoryBits)-1))) & ((1<<ghistoryBits)-1);
      return (gshareBHT[gBHT_idx] >= WT) ? TAKEN : NOTTAKEN;
    case TOURNAMENT:
      // Local prediction
      localOutcome = (localBHT[localPHT[pc & ((1<<pcIndexBits)-1)]] >= WT) ? TAKEN : NOTTAKEN;
      // Global prediction
      globalOutcome = (globalBHT[globalhistory_tour] >= WT) ? TAKEN : NOTTAKEN;
      // Choice
      if (choicePT[globalhistory_tour] >= WT) {
        return localOutcome;
      }
      return globalOutcome;
    case CUSTOM:
    {
      // 1. 通过PC哈希选择一个权重向量
      uint32_t table_index = pc % NUM_WEIGHT_TABLES;
      
      // 2. 计算输出y (点积), 首先加上偏置权重
      int y_out = weights[table_index][0]; 
      
      // 3. 累加其他特征的权重
      // 将历史位(1/0)映射到特征值(+1/-1)进行计算
      for (int i = 0; i < PERCEPTRON_HISTORY_LENGTH; i++) {
        if ((perceptron_ghistory >> i) & 1) { // if history bit is 1 (TAKEN)
          y_out += weights[table_index][i + 1];
        } else { // if history bit is 0 (NOTTAKEN)
          y_out -= weights[table_index][i + 1];
        }
      }
      
      // 4. 根据y_out的符号做预测
      return (y_out >= 0) ? TAKEN : NOTTAKEN;
    }
    default:
      break;
  }

  // If there is not a compatable bpType then return NOTTAKEN
  return NOTTAKEN;
}

// Train the predictor the last outcome
void train_predictor(uint32_t pc, uint8_t outcome)
{
  uint32_t gBHT_idx, localPHT_idx, localBHT_idx;

  switch (bpType) {
    case STATIC:
      return;
    case GSHARE:
      gBHT_idx = (ghistory ^ (pc & ((1<<ghistoryBits)-1))) & ((1<<ghistoryBits)-1);
      shift_prediction(&gshareBHT[gBHT_idx], outcome);
      ghistory = ((ghistory << 1) | outcome) & ((1<<ghistoryBits)-1);
      break;
    case TOURNAMENT:
      // Recalculate local/global predictions to train choice predictor
      localPHT_idx = pc & ((1<<pcIndexBits)-1);
      localBHT_idx = localPHT[localPHT_idx];
      localOutcome = (localBHT[localBHT_idx] >= WT) ? TAKEN : NOTTAKEN;
      globalOutcome = (globalBHT[globalhistory_tour] >= WT) ? TAKEN : NOTTAKEN;

      // Train choice predictor: if local is correct and global is not, prefer local.
      // if global is correct and local is not, prefer global.
      if (localOutcome != globalOutcome) {
          if (localOutcome == outcome) { // Prefer Local
              if (choicePT[globalhistory_tour] < ST) choicePT[globalhistory_tour]++;
          } else { // Prefer Global
              if (choicePT[globalhistory_tour] > SN) choicePT[globalhistory_tour]--;
          }
      }
      
      // Train local predictor
      shift_prediction(&localBHT[localBHT_idx], outcome);
      localPHT[localPHT_idx] = ((localPHT[localPHT_idx] << 1) | outcome) & ((1<<lhistoryBits)-1);
      
      // Train global predictor
      shift_prediction(&globalBHT[globalhistory_tour], outcome);
      globalhistory_tour = ((globalhistory_tour << 1) | outcome) & ((1<<ghistoryBits)-1);
      break;
    case CUSTOM:
    {
      // 1. 重新计算y_out, 与make_prediction中的逻辑完全相同
      uint32_t table_index = pc % NUM_WEIGHT_TABLES;
      int y_out = weights[table_index][0];
      for (int i = 0; i < PERCEPTRON_HISTORY_LENGTH; i++) {
        if ((perceptron_ghistory >> i) & 1) {
          y_out += weights[table_index][i + 1];
        } else {
          y_out -= weights[table_index][i + 1];
        }
      }
      
      uint8_t prediction = (y_out >= 0) ? TAKEN : NOTTAKEN;
      
      // 2. 只有在预测错误, 或预测正确但"信心不足"时, 才更新权重
      if (prediction != outcome || abs(y_out) <= LEARNING_THRESHOLD) {
        int t = (outcome == TAKEN) ? 1 : -1;
        
        // 更新偏置权重 (带饱和)
        if (t == 1 && weights[table_index][0] < MAX_WEIGHT) {
          weights[table_index][0]++;
        } else if (t == -1 && weights[table_index][0] > MIN_WEIGHT) {
          weights[table_index][0]--;
        }
        
        // 更新其他权重 (Perceptron训练法则: w = w + t*x)
        for (int i = 0; i < PERCEPTRON_HISTORY_LENGTH; i++) {
          int x_i = ((perceptron_ghistory >> i) & 1) ? 1 : -1;
          // 当真实结果(t)和历史特征(x_i)相同时, 增加权重; 不同时, 减小权重。
          if (t == x_i) {
            if (weights[table_index][i + 1] < MAX_WEIGHT) weights[table_index][i + 1]++;
          } else {
            if (weights[table_index][i + 1] > MIN_WEIGHT) weights[table_index][i + 1]--;
          }
        }
      }
      
      // 3. 最后, 更新全局历史
      perceptron_ghistory = (perceptron_ghistory << 1) | outcome;
      break;
    }
    default:
      break;
  }
}