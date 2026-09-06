package com.vkr.theaterclient.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.vkr.theaterclient.ui.TheaterViewModel

@Composable
fun ShowsScreen(
    theaterId: Int,
    viewModel: TheaterViewModel,
    onShowClick: (Int) -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(theaterId) {
        viewModel.loadShows(theaterId, state.showDateFilter)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Представления", style = MaterialTheme.typography.headlineSmall)
        OutlinedTextField(
            value = state.showDateFilter,
            onValueChange = viewModel::setShowDateFilter,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Фильтр даты (YYYY-MM-DD)") },
        )
        androidx.compose.material3.Button(
            onClick = { viewModel.loadShows(theaterId, state.showDateFilter) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Применить фильтр") }
        if (state.loading) Text("Загрузка...")
        state.error?.let { Text(text = it, color = MaterialTheme.colorScheme.error) }
        if (!state.loading && state.shows.isEmpty()) {
            Text("Для выбранного театра нет представлений.")
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.shows, key = { it.showId }) { show ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onShowClick(show.showId) },
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(show.title ?: "Без названия")
                        Text(show.showDate ?: "", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}
